// SWGB-DE asset builder: regenerates the SWBG-Data media mod from the
// user's own Star Wars Galactic Battlegrounds Saga + Expanding Fronts install.
//
// Written for the C# 5 compiler that ships with .NET Framework 4.x so that
// Windows PowerShell 5.1 can compile it with Add-Type (no extra runtime needed).
//
// The sprite path is a faithful port of outputs/toolkit/PortSprites.java and of
// the subset of SMX Workshop behaviour it relies on (SLP decode, nearest-colour
// palette mapping, nearest-neighbour scaling, horizontal flip and the SMX
// "8-to-5" writer). Output is byte-identical to the Java pipeline; the recipe
// carries the expected SHA-256 of every generated file.
using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace SwgbDe
{
    public sealed class DrsEntry
    {
        public string Archive;
        public string Type;
        public int Id;
        public long Offset;
        public int Size;
    }

    public static class Drs
    {
        // Index a Genie DRS archive: (type,id) -> entry.
        public static Dictionary<string, DrsEntry> Index(string path)
        {
            var result = new Dictionary<string, DrsEntry>();
            using (var f = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            using (var r = new BinaryReader(f))
            {
                byte[] head = r.ReadBytes(84);
                if (head.Length < 84) throw new InvalidDataException("Short DRS header: " + path);
                int tableCount = BitConverter.ToInt32(head, 76);
                if (tableCount < 0 || tableCount > 100) throw new InvalidDataException("Bad DRS table count: " + path);
                var tables = new List<int[]>();
                var types = new List<string>();
                for (int i = 0; i < tableCount; i++)
                {
                    byte[] ext = r.ReadBytes(4);
                    Array.Reverse(ext);
                    types.Add(Encoding.ASCII.GetString(ext).Trim('\0', ' '));
                    tables.Add(new int[] { r.ReadInt32(), r.ReadInt32() });
                }
                string name = Path.GetFileName(path);
                for (int t = 0; t < tables.Count; t++)
                {
                    f.Position = tables[t][0];
                    for (int i = 0; i < tables[t][1]; i++)
                    {
                        var e = new DrsEntry();
                        e.Archive = name; e.Type = types[t];
                        e.Id = r.ReadInt32(); e.Offset = (uint)r.ReadInt32(); e.Size = r.ReadInt32();
                        if (e.Offset + e.Size > f.Length) throw new InvalidDataException("DRS entry out of range: " + path);
                        result[e.Type + ":" + e.Id] = e;
                    }
                }
            }
            return result;
        }

        public static byte[] Read(string path, DrsEntry e)
        {
            using (var f = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                f.Position = e.Offset;
                byte[] data = new byte[e.Size];
                int read = 0;
                while (read < data.Length)
                {
                    int n = f.Read(data, read, data.Length - read);
                    if (n <= 0) throw new EndOfStreamException(path);
                    read += n;
                }
                return data;
            }
        }
    }

    // JASC-PAL palette, semantics of SMX Workshop's Palette class.
    public sealed class Pal
    {
        public int[] Rgbs;

        public static Pal FromText(string text)
        {
            var lines = text.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');
            int count = int.Parse(lines[2].Trim(), CultureInfo.InvariantCulture);
            int alpha = unchecked((int)0xff000000);
            bool includeAlpha = false;
            string first = lines.Length > 3 ? lines[3] : "";
            if (first.StartsWith("$ALPHA"))
            {
                alpha = int.Parse(first.Substring(7).Trim(), CultureInfo.InvariantCulture) << 24;
                includeAlpha = true;
            }
            var p = new Pal();
            p.Rgbs = new int[count];
            int li = includeAlpha ? 4 : 3;
            for (int i = 0; i < count; i++, li++)
            {
                if (li >= lines.Length) break;
                var fig = lines[li].Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
                if (fig.Length >= 3)
                {
                    int rgb = int.Parse(fig[0], CultureInfo.InvariantCulture);
                    if (rgb < 0) p.Rgbs[i] = 0;
                    else
                    {
                        for (int j = 1; j < 3; j++) rgb = rgb << 8 | int.Parse(fig[j], CultureInfo.InvariantCulture);
                        p.Rgbs[i] = rgb | alpha;
                    }
                }
            }
            return p;
        }

        public static Pal FromBytes(byte[] data) { return FromText(Encoding.ASCII.GetString(data)); }

        public Pal Sub(int start, int length)
        {
            var p = new Pal();
            p.Rgbs = new int[length];
            Array.Copy(Rgbs, start, p.Rgbs, 0, length);
            return p;
        }

        public int Mapping(int argb)
        {
            int red = (argb >> 16) & 0xff, green = (argb >> 8) & 0xff, blue = argb & 0xff;
            double distance = double.PositiveInfinity;
            int mapto = -1;
            for (int j = 0; j < Rgbs.Length; ++j)
            {
                int rgb = Rgbs[j];
                if (rgb == 0) continue;
                int r2 = rgb >> 16 & 0xff, g2 = rgb >> 8 & 0xff, b2 = rgb & 0xff;
                double d = Math.Sqrt(Math.Pow(red - r2, 2) + Math.Pow(green - g2, 2) + Math.Pow(blue - b2, 2));
                if (d < distance)
                {
                    if (distance <= 0) return j;
                    mapto = j; distance = d;
                }
            }
            return mapto;
        }

        public static int[] MappingArray(Pal src, Pal dst)
        {
            int[] map = new int[src.Rgbs.Length];
            for (int i = 0; i < map.Length; i++) map[i] = dst.Mapping(src.Rgbs[i]);
            return map;
        }
    }

    // Port of SMX Workshop's SMXSprite.Frame (only what the converter uses).
    public sealed class Frame
    {
        public const int IMAGE = 0, SHADOW = 1, OUTLINE = 2, SMUDGE = 3;
        public const int NULL = -1;
        public const int PLAYER = 0x1000000;
        const int PLAYER_COLOR_START = -16384;

        public short[] image = new short[0];
        public byte[] shadow = new byte[0];
        public sbyte[] outline = new sbyte[0];
        public short[] smudge = new short[0];
        public int[] props = new int[16];
        public int palette;

        public int W(int t) { return props[t * 4]; }
        public int H(int t) { return props[t * 4 + 1]; }
        public int AX(int t) { return props[t * 4 + 2]; }
        public int AY(int t) { return props[t * 4 + 3]; }

        public Frame Clone()
        {
            var f = new Frame();
            f.image = (short[])image.Clone();
            f.shadow = (byte[])shadow.Clone();
            f.outline = (sbyte[])outline.Clone();
            f.smudge = (short[])smudge.Clone();
            f.props = (int[])props.Clone();
            f.palette = palette;
            return f;
        }

        public int Get(int t, int x, int y)
        {
            switch (t)
            {
                case IMAGE:
                    int v = image[props[0] * y + x];
                    if (v >= 0) return v;
                    if (v <= PLAYER_COLOR_START) return PLAYER_COLOR_START - v + PLAYER;
                    return NULL;
                case SHADOW:
                    byte s = shadow[props[4] * y + x];
                    return s == 0 ? NULL : s;
                case OUTLINE:
                    return outline[props[8] * y + x];
                case SMUDGE:
                    return smudge[props[12] * y + x];
            }
            return NULL;
        }

        public void Set(int t, int x, int y, int value)
        {
            switch (t)
            {
                case IMAGE:
                    if (value < PLAYER) image[props[0] * y + x] = unchecked((short)value);
                    else image[props[0] * y + x] = unchecked((short)(PLAYER_COLOR_START - (value - PLAYER)));
                    break;
                case SHADOW:
                    shadow[props[4] * y + x] = value == NULL ? (byte)0 : unchecked((byte)value);
                    break;
                case OUTLINE:
                    outline[props[8] * y + x] = unchecked((sbyte)value);
                    break;
                case SMUDGE:
                    smudge[props[12] * y + x] = unchecked((short)value);
                    break;
            }
        }

        public void Create(int w, int h)
        {
            int size = w * h;
            image = new short[size]; for (int i = 0; i < size; i++) image[i] = NULL;
            shadow = new byte[size];
            outline = new sbyte[size]; for (int i = 0; i < size; i++) outline[i] = NULL;
            smudge = new short[size]; for (int i = 0; i < size; i++) smudge[i] = NULL;
            for (int t = 0; t < 4; t++) { props[t * 4] = w; props[t * 4 + 1] = h; props[t * 4 + 2] = 0; props[t * 4 + 3] = 0; }
        }

        // Deprecated single-layer create (used for the smudge layer): keeps anchors.
        public void CreateSmudge(int w, int h)
        {
            int size = w * h;
            smudge = new short[size]; for (int i = 0; i < size; i++) smudge[i] = NULL;
            props[12] = w; props[13] = h;
        }

        public void SetAnchor(int t, int x, int y) { props[t * 4 + 2] = x; props[t * 4 + 3] = y; }

        public void FlipHorizontal()
        {
            int width = props[0], limit = width / 2;
            for (int y = 0; y < props[1]; ++y)
            {
                int o = width * y;
                for (int x = 0; x < limit; ++x) { short t = image[o + width - x - 1]; image[o + width - x - 1] = image[o + x]; image[o + x] = t; }
            }
            props[2] = width - props[2];
            width = props[4]; limit = width / 2;
            for (int y = 0; y < props[5]; ++y)
            {
                int o = width * y;
                for (int x = 0; x < limit; ++x) { byte t = shadow[o + width - x - 1]; shadow[o + width - x - 1] = shadow[o + x]; shadow[o + x] = t; }
            }
            props[6] = width - props[6];
            width = props[8]; limit = width / 2;
            for (int y = 0; y < props[9]; ++y)
            {
                int o = width * y;
                for (int x = 0; x < limit; ++x) { sbyte t = outline[o + width - x - 1]; outline[o + width - x - 1] = outline[o + x]; outline[o + x] = t; }
            }
            props[10] = width - props[10];
            width = props[12]; limit = width / 2;
            for (int y = 0; y < props[13]; ++y)
            {
                int o = width * y;
                for (int x = 0; x < limit; ++x) { short t = smudge[o + width - x - 1]; smudge[o + width - x - 1] = smudge[o + x]; smudge[o + x] = t; }
            }
            props[14] = width - props[14];
        }

        public void Scale(double fx, double fy)
        {
            for (int type = 0; type < 4; type++)
            {
                int x0 = props[type * 4 + 2], y0 = props[type * 4 + 3];
                int width0 = props[type * 4], height0 = props[type * 4 + 1];
                int ml = (int)(x0 * fx);
                int mr = (int)((width0 - x0) * fx);
                int mu = (int)(y0 * fy);
                int md = (int)((height0 - y0) * fy);
                int width1 = ml + mr, height1 = mu + md;
                int[] rows = new int[Math.Max(0, height1)];
                int[] columns = new int[Math.Max(0, width1)];
                for (int i = 0; i < height1; ++i) rows[i] = (int)Math.Max(0.0, (i - mu) / fy + y0) * width0;
                for (int i = 0; i < width1; ++i) columns[i] = (int)Math.Max(0.0, (i - ml) / fx + x0);
                int n = Math.Max(0, width1 * height1);
                switch (type)
                {
                    case IMAGE:
                        { var a = new short[n]; for (int y = 0; y < height1; ++y) { int o = y * width1, o0 = rows[y]; for (int x = 0; x < width1; ++x) a[o + x] = image[o0 + columns[x]]; } image = a; }
                        break;
                    case SHADOW:
                        { var a = new byte[n]; for (int y = 0; y < height1; ++y) { int o = y * width1, o0 = rows[y]; for (int x = 0; x < width1; ++x) a[o + x] = shadow[o0 + columns[x]]; } shadow = a; }
                        break;
                    case OUTLINE:
                        { var a = new sbyte[n]; for (int y = 0; y < height1; ++y) { int o = y * width1, o0 = rows[y]; for (int x = 0; x < width1; ++x) a[o + x] = outline[o0 + columns[x]]; } outline = a; }
                        break;
                    case SMUDGE:
                        { var a = new short[n]; for (int y = 0; y < height1; ++y) { int o = y * width1, o0 = rows[y]; for (int x = 0; x < width1; ++x) a[o + x] = smudge[o0 + columns[x]]; } smudge = a; }
                        break;
                }
                props[type * 4] = width1; props[type * 4 + 1] = height1;
                props[type * 4 + 2] = ml; props[type * 4 + 3] = mu;
            }
        }
    }

    public static class Sprites
    {
        static int U32(byte[] d, int o) { return BitConverter.ToInt32(d, o); }
        static int U16(byte[] d, int o) { return BitConverter.ToUInt16(d, o); }

        // Port of PortSprites.loadSLP (offset-aware SLP 2.0N reader).
        public static List<Frame> LoadSlp(byte[] d, string name)
        {
            int count = U32(d, 4);
            var frames = new List<Frame>();
            for (int i = 0; i < count; i++)
            {
                int b0 = 32 + 32 * i;
                int commands = U32(d, b0), outlineOff = U32(d, b0 + 4);
                int w = U32(d, b0 + 16), h = U32(d, b0 + 20), ax = U32(d, b0 + 24), ay = U32(d, b0 + 28);
                var f = new Frame();
                f.Create(w, h);
                f.SetAnchor(Frame.IMAGE, ax, ay); f.SetAnchor(Frame.SHADOW, ax, ay); f.SetAnchor(Frame.OUTLINE, ax, ay);
                frames.Add(f);
                for (int y = 0; y < h; y++)
                {
                    int x = U16(d, outlineOff + 4 * y), right = U16(d, outlineOff + 4 * y + 2);
                    if (x == 32768 || right == 32768) continue;
                    int p = U32(d, commands + 4 * y);
                    while (true)
                    {
                        int b = d[p++], op = b & 15, n = b >> 4, t = 0, px = -1;
                        if (op == 15) break;
                        if ((b & 3) == 0) { n = b >> 2; for (int j = 0; j < n; j++) f.Set(0, x++, y, d[p++]); continue; }
                        if ((b & 3) == 1) { x += b >> 2; continue; }
                        if (op == 2) { n = ((b & 240) << 4) + d[p++]; for (int j = 0; j < n; j++) f.Set(0, x++, y, d[p++]); continue; }
                        if (op == 3) { x += ((b & 240) << 4) + d[p++]; continue; }
                        if (op == 6) { if (n == 0) n = d[p++]; for (int j = 0; j < n; j++) f.Set(0, x++, y, Frame.PLAYER + d[p++]); continue; }
                        if (op == 7 || op == 10 || op == 11)
                        {
                            if (n == 0) n = d[p++];
                            if (op == 11) { t = 1; px = 128; }
                            else px = d[p++] + (op == 10 ? Frame.PLAYER : 0);
                        }
                        else if (b == 78 || b == 94) { t = 2; px = 0; n = b == 78 ? 1 : d[p++]; }
                        else if (b == 110 || b == 126) { n = b == 110 ? 1 : d[p++]; x += n; continue; }
                        else throw new InvalidDataException("Unsupported SLP opcode " + b + " " + name);
                        for (int j = 0; j < n; j++) f.Set(t, x++, y, px);
                    }
                }
            }
            return frames;
        }

        static readonly HashSet<int> FixedPaint = new HashSet<int>(new int[] { 10611, 10612, 10613, 10614, 10615, 16291, 16292 });

        // Port of PortSprites.main for one graphic and one scale.
        public static byte[] Convert(byte[] slp, int gid, int metaFrames, int metaAngles, int metaMirror,
                                     double scaleArg, int[] lut, int[] playerLut)
        {
            var s = LoadSlp(slp, gid + ".slp");
            if (s.Count == 0) throw new InvalidDataException("Empty " + gid);
            if (FixedPaint.Contains(gid))
            {
                foreach (var f in s)
                    for (int y = 0; y < f.H(0); y++)
                        for (int x = 0; x < f.W(0); x++)
                        {
                            int p = f.Get(0, x, y) - Frame.PLAYER;
                            if (p >= 8)
                            {
                                if (p > 15) throw new InvalidDataException("Unexpected extended player shade " + p);
                                f.Set(0, x, y, 16 + p);
                            }
                        }
            }
            var conv = new List<Frame>();
            bool empty = true;
            foreach (var f in s)
                for (int t = 0; t < 3 && empty; t++)
                    for (int y = 0; y < f.H(t) && empty; y++)
                        for (int x = 0; x < f.W(t); x++)
                            if (f.Get(t, x, y) != -1) { empty = false; break; }
            if (empty)
            {
                for (int k = 0; k < metaFrames * metaAngles; k++) conv.Add(s[0].Clone());
            }
            else if (metaAngles == 8 || metaAngles == 16)
            {
                int angles = metaAngles, half = angles / 2;
                bool mirrored = metaMirror != 0;
                int sourceFrames = metaFrames;
                if (gid == 5582 && s.Count == 5 && mirrored && angles == 8) sourceFrames = 1;
                if (s.Count != sourceFrames * (mirrored ? half + 1 : angles)) throw new InvalidDataException("Direction/frame count mismatch: " + gid);
                for (int angle = 0; angle < angles; angle++)
                {
                    int direction = (angle - angles / 4 + angles) % angles;
                    int group = mirrored ? (direction <= half ? direction : angles - direction) : direction;
                    for (int k = 0; k < metaFrames; k++)
                    {
                        var f = s[group * sourceFrames + k % sourceFrames].Clone();
                        if (mirrored && direction > half) f.FlipHorizontal();
                        conv.Add(f);
                    }
                }
            }
            else if (metaAngles == 1 || metaAngles == 3 || metaAngles == 5)
            {
                if (s.Count < metaFrames * metaAngles) throw new InvalidDataException("Variation/stage count mismatch: " + gid);
                foreach (var f in s) conv.Add(f.Clone());
            }
            else if (metaMirror == 0 && (metaAngles == 2 || metaAngles == 6 || metaAngles == 10 || metaAngles == 11 || metaAngles == 12 || metaAngles == 22 || metaAngles == 24))
            {
                if (s.Count < metaFrames * metaAngles) throw new InvalidDataException("Resource variation count mismatch: " + gid);
                foreach (var f in s) conv.Add(f.Clone());
            }
            else throw new InvalidDataException("Unsupported angle count: " + metaAngles + " " + gid);

            double scale = scaleArg;
            if (gid == 13106 || gid == 11805) scale *= 3.0;
            foreach (var f in conv)
            {
                int w = f.W(0), h = f.H(0);
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++)
                    {
                        int p = f.Get(0, x, y);
                        if (p != Frame.NULL && p < Frame.PLAYER) f.Set(0, x, y, lut[p]);
                    }
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++)
                    {
                        int p = f.Get(0, x, y);
                        if (p != Frame.NULL && p >= Frame.PLAYER) f.Set(0, x, y, playerLut[p - Frame.PLAYER] + Frame.PLAYER);
                    }
                f.palette = 0;
                f.Scale(scale, scale);
            }
            // Neutral DE damage values for every visible pixel.
            foreach (var f in conv)
            {
                int w = f.W(0), h = f.H(0);
                if (w == 0 || h == 0) continue;
                f.CreateSmudge(w, h);
                f.SetAnchor(Frame.SMUDGE, f.AX(0), f.AY(0));
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++)
                        if (f.Get(0, x, y) != Frame.NULL) f.Set(Frame.SMUDGE, x, y, 0);
            }
            return Smx.Save(conv);
        }
    }

    // Port of SMX Workshop's CompiledSMXFrame + saveSMXSprite.
    public static class Smx
    {
        sealed class Compiled
        {
            public int smpSize;
            public int[] padImage, padOutline, padShadow;
            public byte[] mapImage, dataImage, dataOutline, dataShadow;
            public Frame frame;
        }

        static int Rgb555(int index)
        {
            int red = ((index & 0x7c00) >> 7) * 0xff / 0xf8,
                green = ((index & 0x3e0) >> 2) * 0xff / 0xf8,
                blue = ((index & 0x1f) << 3) * 0xff / 0xf8;
            return red << 16 | green << 8 | blue | unchecked((int)0xff000000);
        }

        static Compiled Compile(Frame frame)
        {
            var c = new Compiled();
            c.frame = frame;
            c.smpSize = 0;
            int width = frame.W(Frame.IMAGE), height = frame.H(Frame.IMAGE);
            byte[] mapImage = new byte[(width + 1) * height];
            if (height > 0)
            {
                c.smpSize += 32 + height * 8;
                if (frame.H(Frame.SMUDGE) > 0)
                {
                    byte[] dataImage = new byte[width * height * 5 / 2 + 5];
                    c.padImage = new int[height * 2];
                    int offset = 0, offset1 = 0, counter = 0;
                    for (int y = 0; y < height; ++y)
                    {
                        int left = 0, right = width - 1;
                        while (left < width && frame.Get(Frame.IMAGE, left, y) == Frame.NULL) ++left;
                        if (left >= width) { c.padImage[y * 2] = -1; c.padImage[y * 2 + 1] = -1; continue; }
                        while (frame.Get(Frame.IMAGE, right, y) == Frame.NULL) --right;
                        c.padImage[y * 2] = left; c.padImage[y * 2 + 1] = width - right - 1;
                        for (int x = left; x <= right; )
                        {
                            int pixel = frame.Get(Frame.IMAGE, x, y);
                            int limit = Math.Min(right, x + 0x3f);
                            if (pixel == Frame.NULL)
                            {
                                int x1 = x + 1;
                                for (; x1 <= limit; ++x1) if (frame.Get(Frame.IMAGE, x1, y) != Frame.NULL) break;
                                mapImage[offset++] = unchecked((byte)(x1 - x - 1 << 2));
                                x = x1;
                            }
                            else
                            {
                                bool player = pixel >= Frame.PLAYER;
                                int x1 = x + 1;
                                for (; x1 <= limit; ++x1)
                                {
                                    pixel = frame.Get(Frame.IMAGE, x1, y);
                                    if (pixel == Frame.NULL || (player ? pixel < Frame.PLAYER : pixel >= Frame.PLAYER)) break;
                                }
                                int length = x1 - x;
                                mapImage[offset++] = unchecked((byte)(length - 1 << 2 | (player ? 0x2 : 0x1)));
                                c.smpSize += length << 2;
                                for (; length > 0; ++x, --length, ++counter)
                                {
                                    pixel = frame.Get(Frame.IMAGE, x, y) - (player ? Frame.PLAYER : 0);
                                    int smudgeColor = Rgb555(frame.Get(Frame.SMUDGE, x, y));
                                    int smudge = ((smudgeColor & 0xff) + ((smudgeColor >> 8) & 0xff) + ((smudgeColor >> 16) & 0xff)) * 1023 / 255;
                                    if ((counter & 1) == 0)
                                    {
                                        dataImage[offset1] = unchecked((byte)(pixel & 0xff));
                                        dataImage[offset1 + 1] = unchecked((byte)(pixel >> 8 & 0x3));
                                        dataImage[offset1 + 2] = unchecked((byte)(smudge << 4 & 0xf0));
                                        dataImage[offset1 + 3] = unchecked((byte)(smudge >> 4 & 0x3f));
                                        ++offset1;
                                    }
                                    else
                                    {
                                        dataImage[offset1] |= unchecked((byte)(pixel << 2 & 0xfc));
                                        dataImage[offset1 + 1] |= unchecked((byte)(pixel >> 6 & 0xf));
                                        dataImage[offset1 + 2] |= unchecked((byte)(smudge << 6 & 0xc0));
                                        dataImage[offset1 + 3] = unchecked((byte)(smudge >> 2 & 0xff));
                                        offset1 += 4;
                                    }
                                }
                            }
                            ++c.smpSize;
                        }
                        mapImage[offset++] = 0x3;
                        ++c.smpSize;
                    }
                    c.mapImage = new byte[offset]; Array.Copy(mapImage, c.mapImage, offset);
                    offset1 = (counter + 1) / 2 * 5;
                    c.dataImage = new byte[offset1]; Array.Copy(dataImage, c.dataImage, offset1);
                }
                else
                {
                    byte[] dataImage = new byte[width * height * 5 / 4 + 5];
                    c.padImage = new int[height * 2];
                    int offset = 0, offset1 = 0, offset2 = 4;
                    for (int y = 0; y < height; ++y)
                    {
                        int left = 0, right = width - 1;
                        while (left < width && frame.Get(Frame.IMAGE, left, y) == Frame.NULL) ++left;
                        if (left >= width) { c.padImage[y * 2] = -1; c.padImage[y * 2 + 1] = -1; continue; }
                        while (frame.Get(Frame.IMAGE, right, y) == Frame.NULL) --right;
                        c.padImage[y * 2] = left; c.padImage[y * 2 + 1] = width - right - 1;
                        for (int x = left; x <= right; )
                        {
                            int pixel = frame.Get(Frame.IMAGE, x, y);
                            int limit = Math.Min(right, x + 0x3f);
                            if (pixel == Frame.NULL)
                            {
                                int x1 = x + 1;
                                for (; x1 <= limit; ++x1) if (frame.Get(Frame.IMAGE, x1, y) != Frame.NULL) break;
                                mapImage[offset++] = unchecked((byte)(x1 - x - 1 << 2));
                                x = x1;
                            }
                            else
                            {
                                bool player = pixel >= Frame.PLAYER;
                                int x1 = x + 1;
                                for (; x1 <= limit; ++x1)
                                {
                                    pixel = frame.Get(Frame.IMAGE, x1, y);
                                    if (pixel == Frame.NULL || (player ? pixel < Frame.PLAYER : pixel >= Frame.PLAYER)) break;
                                }
                                int length = x1 - x;
                                mapImage[offset++] = unchecked((byte)(length - 1 << 2 | (player ? 0x2 : 0x1)));
                                c.smpSize += length << 2;
                                for (; length > 0; ++x, --length)
                                {
                                    pixel = frame.Get(Frame.IMAGE, x, y) - (player ? Frame.PLAYER : 0);
                                    dataImage[offset2] |= unchecked((byte)((pixel & 0x300) >> 2 * (offset2 - offset1)));
                                    dataImage[offset1++] = unchecked((byte)pixel);
                                    if (offset1 == offset2) { ++offset1; offset2 += 5; }
                                }
                            }
                            ++c.smpSize;
                        }
                        mapImage[offset++] = 0x3;
                        ++c.smpSize;
                    }
                    c.mapImage = new byte[offset]; Array.Copy(mapImage, c.mapImage, offset);
                    c.dataImage = new byte[offset2 + 1]; Array.Copy(dataImage, c.dataImage, offset2 + 1);
                }
            }

            // Shadow
            width = frame.W(Frame.SHADOW); height = frame.H(Frame.SHADOW);
            {
                byte[] dataShadow = new byte[(width + 1) * height * 2];
                c.padShadow = new int[height * 2];
                if (height > 0)
                {
                    c.smpSize += 32 + height * 8;
                    int offset = 0;
                    for (int y = 0; y < height; ++y)
                    {
                        int left = 0, right = width - 1;
                        while (left < width && frame.Get(Frame.SHADOW, left, y) == Frame.NULL) ++left;
                        if (left >= width) { c.padShadow[y * 2] = -1; c.padShadow[y * 2 + 1] = -1; continue; }
                        while (frame.Get(Frame.SHADOW, right, y) == Frame.NULL) --right;
                        c.padShadow[y * 2] = left; c.padShadow[y * 2 + 1] = width - right - 1;
                        for (int x = left; x <= right; )
                        {
                            int pixel = frame.Get(Frame.SHADOW, x, y);
                            int limit = Math.Min(right, x + 0x3f);
                            if (pixel == Frame.NULL)
                            {
                                int x1 = x + 1;
                                for (; x1 <= limit; ++x1) if (frame.Get(Frame.SHADOW, x1, y) != Frame.NULL) break;
                                dataShadow[offset++] = unchecked((byte)(x1 - x - 1 << 2));
                                x = x1;
                            }
                            else
                            {
                                int x1 = x + 1;
                                for (; x1 <= limit; ++x1) if (frame.Get(Frame.SHADOW, x1, y) == Frame.NULL) break;
                                int length = x1 - x;
                                dataShadow[offset++] = unchecked((byte)(length - 1 << 2 | 0x1));
                                c.smpSize += length;
                                for (; length > 0; ++x, --length) dataShadow[offset++] = unchecked((byte)frame.Get(Frame.SHADOW, x, y));
                            }
                            ++c.smpSize;
                        }
                        dataShadow[offset++] = 0x3;
                        ++c.smpSize;
                    }
                    c.dataShadow = new byte[offset]; Array.Copy(dataShadow, c.dataShadow, offset);
                }
            }

            // Outline
            width = frame.W(Frame.OUTLINE); height = frame.H(Frame.OUTLINE);
            {
                byte[] dataOutline = new byte[width * height * 2];
                c.padOutline = new int[height * 2];
                if (height > 0)
                {
                    c.smpSize += 32 + height * 8;
                    int offset = 0;
                    for (int y = 0; y < height; ++y)
                    {
                        int left = 0, right = width - 1;
                        while (left < width && frame.Get(Frame.OUTLINE, left, y) == Frame.NULL) ++left;
                        if (left >= width) { c.padOutline[y * 2] = -1; c.padOutline[y * 2 + 1] = -1; continue; }
                        while (frame.Get(Frame.OUTLINE, right, y) == Frame.NULL) --right;
                        c.padOutline[y * 2] = left; c.padOutline[y * 2 + 1] = width - right - 1;
                        for (int x = left; x <= right; )
                        {
                            int pixel = frame.Get(Frame.OUTLINE, x, y);
                            int limit = Math.Min(right, x + 0x3f);
                            int x1 = x + 1;
                            if (pixel == Frame.NULL)
                            {
                                for (; x1 <= limit; ++x1) if (frame.Get(Frame.OUTLINE, x1, y) != Frame.NULL) break;
                                dataOutline[offset++] = unchecked((byte)(x1 - x - 1 << 2));
                            }
                            else
                            {
                                for (; x1 <= limit; ++x1) if (frame.Get(Frame.OUTLINE, x1, y) == Frame.NULL) break;
                                dataOutline[offset++] = unchecked((byte)(x1 - x - 1 << 2 | 0x1));
                            }
                            x = x1;
                            ++c.smpSize;
                        }
                        dataOutline[offset++] = 0x3;
                        ++c.smpSize;
                    }
                    c.dataOutline = new byte[offset]; Array.Copy(dataOutline, c.dataOutline, offset);
                }
            }
            c.smpSize = (c.smpSize + 63) & unchecked((int)0xffffffc0);
            return c;
        }

        static void W16(Stream s, int v) { s.WriteByte((byte)v); s.WriteByte((byte)(v >> 8)); }
        static void W32(Stream s, int v) { s.WriteByte((byte)v); s.WriteByte((byte)(v >> 8)); s.WriteByte((byte)(v >> 16)); s.WriteByte((byte)(v >> 24)); }

        public static byte[] Save(List<Frame> frames)
        {
            int count = frames.Count;
            int[] sizes = new int[count * 3];
            byte[] flags = new byte[count];
            var compiled = new Compiled[count];
            int size = 0, smpSize = count * 4;
            for (int i = 0; i < count; ++i)
            {
                var c = Compile(frames[i]);
                var f = c.frame;
                flags[i] = 0;
                if (f.H(Frame.IMAGE) > 0)
                {
                    sizes[i * 3] = c.mapImage.Length + c.dataImage.Length + f.H(Frame.IMAGE) * 4 + 8;
                    size += sizes[i * 3] + 16;
                    flags[i] |= 1;
                    if (f.H(Frame.SMUDGE) > 0) flags[i] |= 8;
                }
                if (f.H(Frame.SHADOW) > 0)
                {
                    sizes[i * 3 + 1] = c.dataShadow.Length + f.H(Frame.SHADOW) * 4 + 4;
                    size += sizes[i * 3 + 1] + 16;
                    flags[i] |= 2;
                }
                if (f.H(Frame.OUTLINE) > 0)
                {
                    sizes[i * 3 + 2] = c.dataOutline.Length + f.H(Frame.OUTLINE) * 4 + 4;
                    size += sizes[i * 3 + 2] + 16;
                    flags[i] |= 4;
                }
                size += 6;
                smpSize += c.smpSize;
                compiled[i] = c;
            }
            var ms = new MemoryStream();
            ms.Write(Encoding.ASCII.GetBytes("SMPX"), 0, 4);
            W16(ms, 2); W16(ms, count); W32(ms, size); W32(ms, smpSize);
            byte[] memo = Encoding.ASCII.GetBytes("ArtDesk 1.00 SLP");
            ms.Write(memo, 0, 16);
            for (int i = 0; i < count; ++i)
            {
                var c = compiled[i];
                var f = c.frame;
                byte flag = flags[i];
                ms.WriteByte(flag);
                ms.WriteByte((byte)f.palette);
                W32(ms, c.smpSize);
                if ((flag & 1) != 0)
                {
                    int h = f.H(Frame.IMAGE);
                    W16(ms, f.W(Frame.IMAGE)); W16(ms, h); W16(ms, f.AX(Frame.IMAGE)); W16(ms, f.AY(Frame.IMAGE));
                    W32(ms, sizes[i * 3]); W32(ms, 0);
                    for (int y = 0; y < h; ++y) { W16(ms, c.padImage[y * 2]); W16(ms, c.padImage[y * 2 + 1]); }
                    W32(ms, c.mapImage.Length); W32(ms, c.dataImage.Length);
                    ms.Write(c.mapImage, 0, c.mapImage.Length);
                    ms.Write(c.dataImage, 0, c.dataImage.Length);
                }
                if ((flag & 2) != 0)
                {
                    int h = f.H(Frame.SHADOW);
                    W16(ms, f.W(Frame.SHADOW)); W16(ms, h); W16(ms, f.AX(Frame.SHADOW)); W16(ms, f.AY(Frame.SHADOW));
                    W32(ms, sizes[i * 3 + 1]); W32(ms, 0);
                    for (int y = 0; y < h; ++y) { W16(ms, c.padShadow[y * 2]); W16(ms, c.padShadow[y * 2 + 1]); }
                    W32(ms, c.dataShadow.Length);
                    ms.Write(c.dataShadow, 0, c.dataShadow.Length);
                }
                if ((flag & 4) != 0)
                {
                    int h = f.H(Frame.OUTLINE);
                    W16(ms, f.W(Frame.OUTLINE)); W16(ms, h); W16(ms, f.AX(Frame.OUTLINE)); W16(ms, f.AY(Frame.OUTLINE));
                    W32(ms, sizes[i * 3 + 2]); W32(ms, 0);
                    for (int y = 0; y < h; ++y) { W16(ms, c.padOutline[y * 2]); W16(ms, c.padOutline[y * 2 + 1]); }
                    W32(ms, c.dataOutline.Length);
                    ms.Write(c.dataOutline, 0, c.dataOutline.Length);
                }
            }
            return ms.ToArray();
        }
    }

    // Minimal JSON reader (objects -> Dictionary, arrays -> List, numbers -> double).
    public static class Json
    {
        public static object Parse(string s) { int i = 0; return Value(s, ref i); }
        static void Ws(string s, ref int i) { while (i < s.Length && char.IsWhiteSpace(s[i])) i++; }
        static bool At(string s, int i, string word) { return string.CompareOrdinal(s, i, word, 0, word.Length) == 0; }
        static object Value(string s, ref int i)
        {
            Ws(s, ref i);
            char c = s[i];
            if (c == '{')
            {
                var d = new Dictionary<string, object>(); i++; Ws(s, ref i);
                if (s[i] == '}') { i++; return d; }
                while (true)
                {
                    Ws(s, ref i); string k = Str(s, ref i); Ws(s, ref i);
                    if (s[i] != ':') throw new FormatException("JSON ':' expected at " + i);
                    i++;
                    d[k] = Value(s, ref i); Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == '}') { i++; return d; }
                    throw new FormatException("JSON object at " + i);
                }
            }
            if (c == '[')
            {
                var l = new List<object>(); i++; Ws(s, ref i);
                if (s[i] == ']') { i++; return l; }
                while (true)
                {
                    l.Add(Value(s, ref i)); Ws(s, ref i);
                    if (s[i] == ',') { i++; continue; }
                    if (s[i] == ']') { i++; return l; }
                    throw new FormatException("JSON array at " + i);
                }
            }
            if (c == '"') return Str(s, ref i);
            if (At(s, i, "true")) { i += 4; return true; }
            if (At(s, i, "false")) { i += 5; return false; }
            if (At(s, i, "null")) { i += 4; return null; }
            int st = i;
            while (i < s.Length && "+-0123456789.eE".IndexOf(s[i]) >= 0) i++;
            return double.Parse(s.Substring(st, i - st), CultureInfo.InvariantCulture);
        }
        static string Str(string s, ref int i)
        {
            if (s[i] != '"') throw new FormatException("JSON string expected at " + i);
            i++;
            var sb = new StringBuilder();
            while (s[i] != '"')
            {
                char c = s[i++];
                if (c == '\\')
                {
                    char e = s[i++];
                    if (e == 'n') sb.Append('\n');
                    else if (e == 't') sb.Append('\t');
                    else if (e == 'r') sb.Append('\r');
                    else if (e == 'b') sb.Append('\b');
                    else if (e == 'f') sb.Append('\f');
                    else if (e == 'u') { sb.Append((char)int.Parse(s.Substring(i, 4), NumberStyles.HexNumber)); i += 4; }
                    else sb.Append(e);
                }
                else sb.Append(c);
            }
            i++;
            return sb.ToString();
        }
    }

    public static class Audio
    {
        public static Dictionary<string, byte[]> Chunks(byte[] data)
        {
            if (data.Length < 12 || Encoding.ASCII.GetString(data, 0, 4) != "RIFF" || Encoding.ASCII.GetString(data, 8, 4) != "WAVE")
                throw new InvalidDataException("Not RIFF/WAVE");
            var result = new Dictionary<string, byte[]>();
            int offset = 12;
            while (offset + 8 <= data.Length)
            {
                string key = Encoding.ASCII.GetString(data, offset, 4);
                int size = BitConverter.ToInt32(data, offset + 4);
                if (size < 0 || offset + 8 + (long)size > data.Length) throw new InvalidDataException("Truncated WAV chunk");
                var b = new byte[size];
                Array.Copy(data, offset + 8, b, 0, size);
                result[key] = b;
                offset += 8 + size + (size & 1);
            }
            return result;
        }

        static void Chunk(MemoryStream ms, string name, byte[] data)
        {
            ms.Write(Encoding.ASCII.GetBytes(name), 0, 4);
            ms.Write(BitConverter.GetBytes(data.Length), 0, 4);
            ms.Write(data, 0, data.Length);
            if ((data.Length & 1) != 0) ms.WriteByte(0);
        }

        static byte[] Fmt(int channels, int rate)
        {
            int align = channels * 2;
            int config = ((channels == 1 ? 4 : 3) << 12) | (1 << 8) | channels;
            var ms = new MemoryStream();
            var w = new BinaryWriter(ms);
            w.Write((ushort)0xfffe); w.Write((ushort)channels); w.Write(rate); w.Write(rate * align);
            w.Write((ushort)align); w.Write((ushort)16); w.Write((ushort)6); w.Write((ushort)16); w.Write(config);
            w.Flush();
            return ms.ToArray();
        }

        // Port of encode_faction_pcm.convert: lossless Wwise PCM container.
        public static byte[] WavToWem(byte[] wav)
        {
            var parts = Chunks(wav);
            byte[] fmt = parts["fmt "];
            int tag = BitConverter.ToUInt16(fmt, 0), channels = BitConverter.ToUInt16(fmt, 2);
            int rate = BitConverter.ToInt32(fmt, 4), byteRate = BitConverter.ToInt32(fmt, 8);
            int align = BitConverter.ToUInt16(fmt, 12), bits = BitConverter.ToUInt16(fmt, 14);
            if (!(tag == 1 && bits == 16 && (channels == 1 || channels == 2) && align == channels * 2 && byteRate == rate * align))
                throw new InvalidDataException("Unsupported WAV format");
            var body = new MemoryStream();
            body.Write(Encoding.ASCII.GetBytes("WAVE"), 0, 4);
            Chunk(body, "fmt ", Fmt(channels, rate));
            if (parts.ContainsKey("smpl")) Chunk(body, "smpl", parts["smpl"]);
            Chunk(body, "data", parts["data"]);
            var outMs = new MemoryStream();
            outMs.Write(Encoding.ASCII.GetBytes("RIFF"), 0, 4);
            outMs.Write(BitConverter.GetBytes((int)body.Length), 0, 4);
            body.WriteTo(outMs);
            return outMs.ToArray();
        }

        // Port of faction_music.write_wem (no padding, no smpl chunk).
        public static void WriteMusicWem(string path, Stream pcm, long pcmBytes, int rate, int channels)
        {
            byte[] fmt = Fmt(channels, rate);
            using (var f = new FileStream(path, FileMode.Create, FileAccess.Write))
            {
                var head = new MemoryStream();
                head.Write(Encoding.ASCII.GetBytes("RIFF"), 0, 4);
                head.Write(BitConverter.GetBytes((int)(4 + 8 + fmt.Length + 8 + pcmBytes)), 0, 4);
                head.Write(Encoding.ASCII.GetBytes("WAVE"), 0, 4);
                head.Write(Encoding.ASCII.GetBytes("fmt "), 0, 4);
                head.Write(BitConverter.GetBytes(fmt.Length), 0, 4);
                head.Write(fmt, 0, fmt.Length);
                head.Write(Encoding.ASCII.GetBytes("data"), 0, 4);
                head.Write(BitConverter.GetBytes((int)pcmBytes), 0, 4);
                byte[] h = head.ToArray();
                f.Write(h, 0, h.Length);
                byte[] buf = new byte[1 << 20];
                long left = pcmBytes;
                while (left > 0)
                {
                    int n = pcm.Read(buf, 0, (int)Math.Min(buf.Length, left));
                    if (n <= 0) throw new EndOfStreamException("PCM stream ended early");
                    f.Write(buf, 0, n);
                    left -= n;
                }
            }
        }

        // Locate the PCM data of a decoded WAV file (vgmstream output).
        public static void WavInfo(string path, out long dataOffset, out long dataBytes, out int rate, out int channels, out int bits)
        {
            using (var f = new FileStream(path, FileMode.Open, FileAccess.Read))
            using (var r = new BinaryReader(f))
            {
                if (Encoding.ASCII.GetString(r.ReadBytes(4)) != "RIFF") throw new InvalidDataException("Not RIFF: " + path);
                r.ReadInt32();
                if (Encoding.ASCII.GetString(r.ReadBytes(4)) != "WAVE") throw new InvalidDataException("Not WAVE: " + path);
                rate = channels = bits = 0; dataOffset = dataBytes = -1;
                while (f.Position + 8 <= f.Length)
                {
                    string key = Encoding.ASCII.GetString(r.ReadBytes(4));
                    long size = r.ReadUInt32();
                    long start = f.Position;
                    if (key == "fmt ")
                    {
                        r.ReadUInt16(); channels = r.ReadUInt16(); rate = r.ReadInt32(); r.ReadInt32(); r.ReadUInt16(); bits = r.ReadUInt16();
                    }
                    else if (key == "data") { dataOffset = start; dataBytes = Math.Min(size, f.Length - start); break; }
                    f.Position = start + size + (size & 1);
                }
                if (dataOffset < 0) throw new InvalidDataException("No data chunk: " + path);
            }
        }
    }

    public static class Icons
    {
        // RGBA rendering of one interface SLP frame (PortIcons/RenderInterfaceSheet).
        public static byte[] Render(List<Frame> sheet, int frame, Pal palette, out int w, out int h)
        {
            var f = sheet[frame];
            w = f.W(0); h = f.H(0);
            var px = new byte[w * h * 4];
            for (int y = 0; y < h; y++)
                for (int x = 0; x < w; x++)
                {
                    int p = f.Get(0, x, y);
                    if (p == Frame.NULL) continue;
                    if (p >= Frame.PLAYER) p = p - Frame.PLAYER + 16;
                    int c = palette.Rgbs[p];
                    int o = (y * w + x) * 4;
                    px[o] = (byte)(c >> 16); px[o + 1] = (byte)(c >> 8); px[o + 2] = (byte)c; px[o + 3] = 255;
                }
            return px;
        }

        // Pillow Image.resize(NEAREST): affine scale with accumulated sample coordinates.
        public static byte[] Resize(byte[] src, int sw, int sh, int dw, int dh)
        {
            if (sw == dw && sh == dh) return (byte[])src.Clone();
            var dst = new byte[dw * dh * 4];
            double ax = (double)sw / dw, ay = (double)sh / dh;
            int[] xin = new int[dw];
            double xo = ax * 0.5;
            for (int x = 0; x < dw; x++) { xin[x] = xo < 0 ? -1 : (int)xo; xo += ax; }
            double yo = ay * 0.5;
            for (int y = 0; y < dh; y++)
            {
                int yi = yo < 0 ? -1 : (int)yo;
                yo += ay;
                if (yi < 0 || yi >= sh) continue;
                for (int x = 0; x < dw; x++)
                {
                    int xi = xin[x];
                    if (xi < 0 || xi >= sw) continue;
                    Buffer.BlockCopy(src, (yi * sw + xi) * 4, dst, (y * dw + x) * 4, 4);
                }
            }
            return dst;
        }
    }

    public static class Dds
    {
        public static byte[] RgbaHeader(int w, int h)
        {
            var b = new byte[128];
            Encoding.ASCII.GetBytes("DDS ").CopyTo(b, 0);
            BitConverter.GetBytes(124).CopyTo(b, 4);
            BitConverter.GetBytes(0x2100f).CopyTo(b, 8);
            BitConverter.GetBytes(h).CopyTo(b, 12);
            BitConverter.GetBytes(w).CopyTo(b, 16);
            BitConverter.GetBytes(w * 4).CopyTo(b, 20);
            BitConverter.GetBytes(1).CopyTo(b, 28);
            int[] pf = { 32, 0x41, 0, 32, 0xff, 0xff00, 0xff0000, unchecked((int)0xff000000) };
            for (int i = 0; i < 8; i++) BitConverter.GetBytes(pf[i]).CopyTo(b, 76 + 4 * i);
            BitConverter.GetBytes(0x1000).CopyTo(b, 108);
            return b;
        }

        // Read an uncompressed 32-bit DDS written by texconv as RGBA bytes.
        public static byte[] ReadRgba(string path, out int w, out int h)
        {
            byte[] d = File.ReadAllBytes(path);
            h = BitConverter.ToInt32(d, 12); w = BitConverter.ToInt32(d, 16);
            bool dx10 = Encoding.ASCII.GetString(d, 84, 4) == "DX10";
            int header = dx10 ? 148 : 128;
            if (d.Length < header + (long)w * h * 4) throw new InvalidDataException("Short DDS " + path);
            var px = new byte[w * h * 4];
            Buffer.BlockCopy(d, header, px, 0, px.Length);
            if (!dx10 && BitConverter.ToInt32(d, 92) == 0xff0000)
                for (int i = 0; i < px.Length; i += 4) { byte t = px[i]; px[i] = px[i + 2]; px[i + 2] = t; }
            return px;
        }
    }

    public sealed class AtlasTexture
    {
        public string RefName, FileName;
        public double TLX, TLY, BRX, BRY;
        public int[] Box(int w, int h)
        {
            return new int[] {
                (int)Math.Round(TLX * w - .5), (int)Math.Round(TLY * h - .5),
                (int)Math.Round(BRX * w + .5), (int)Math.Round(BRY * h + .5) };
        }
    }

    public static class Materials
    {
        // Atlas name -> textures, from a DE widgetui/materials.json.
        public static Dictionary<string, List<AtlasTexture>> Atlases(string path)
        {
            var root = (Dictionary<string, object>)Json.Parse(File.ReadAllText(path));
            var result = new Dictionary<string, List<AtlasTexture>>();
            foreach (var item in (List<object>)root["AtlasTextures"])
            {
                var def = (Dictionary<string, object>)((Dictionary<string, object>)item)["AtlasDef"];
                var list = new List<AtlasTexture>();
                object textures;
                if (def.TryGetValue("Textures", out textures) && textures != null)
                    foreach (var t in (List<object>)textures)
                    {
                        var d = (Dictionary<string, object>)t;
                        var a = new AtlasTexture();
                        a.RefName = (string)d["RefName"]; a.FileName = d.ContainsKey("FileName") ? (string)d["FileName"] : "";
                        a.TLX = Num(d["imageTLX"]); a.TLY = Num(d["imageTLY"]); a.BRX = Num(d["imageBRX"]); a.BRY = Num(d["imageBRY"]);
                        list.Add(a);
                    }
                result[(string)def["Name"]] = list;
            }
            return result;
        }
        static double Num(object o) { return o is string ? double.Parse((string)o, CultureInfo.InvariantCulture) : Convert.ToDouble(o, CultureInfo.InvariantCulture); }
    }

    public sealed class Runner
    {
        public string GameDir, DeDir, DataOut, ToolsDir, TempDir, RecipePath, LogicMaterials, ReportPath;
        public int MaxThreads = Math.Max(1, Math.Min(Environment.ProcessorCount, 8));
        public int Exact, Differs, SourceDiffers, Rebuilt, Errors;
        readonly object gate = new object();
        readonly List<string> report = new List<string>();
        readonly Dictionary<string, Dictionary<string, DrsEntry>> drs = new Dictionary<string, Dictionary<string, DrsEntry>>(StringComparer.OrdinalIgnoreCase);
        readonly Dictionary<string, byte[]> iconSource = new Dictionary<string, byte[]>();
        readonly Dictionary<string, int[]> iconSize = new Dictionary<string, int[]>();
        Pal palette;

        void Log(string s) { lock (gate) { Console.WriteLine(s); } }

        static string Sha(byte[] d) { using (var h = SHA256.Create()) return Hex(h.ComputeHash(d)); }
        static string ShaFile(string p) { using (var h = SHA256.Create()) using (var f = File.OpenRead(p)) return Hex(h.ComputeHash(f)); }
        static string Hex(byte[] b) { var sb = new StringBuilder(b.Length * 2); foreach (var x in b) sb.Append(x.ToString("x2")); return sb.ToString(); }

        string DataPath(string archive) { return Path.Combine(GameDir, "Data", archive); }

        byte[] Entry(string archive, string type, int id)
        {
            Dictionary<string, DrsEntry> idx;
            lock (gate)
            {
                if (!drs.TryGetValue(archive, out idx))
                {
                    string p = DataPath(archive);
                    if (!File.Exists(p)) throw new FileNotFoundException("Missing SWGB archive " + p);
                    idx = Drs.Index(p);
                    drs[archive] = idx;
                }
            }
            DrsEntry e;
            if (!idx.TryGetValue(type + ":" + id, out e)) throw new KeyNotFoundException(archive + " has no " + type + " " + id);
            return Drs.Read(DataPath(archive), e);
        }

        string Out(string rel)
        {
            string p = Path.Combine(DataOut, rel.Replace('/', '\\'));
            Directory.CreateDirectory(Path.GetDirectoryName(p));
            return p;
        }

        void Record(string rel, string status, string sha, string note)
        {
            lock (gate)
            {
                report.Add(rel + "\t" + status + "\t" + sha + "\t" + note);
                if (status == "exact") Exact++;
                else if (status == "differs") Differs++;
                else if (status == "source-differs") SourceDiffers++;
                else if (status == "rebuilt") Rebuilt++;
                else if (status == "error") Errors++;
            }
        }

        void Check(string rel, byte[] data, string expected, bool sourceOk)
        {
            string s = Sha(data);
            File.WriteAllBytes(Out(rel), data);
            Record(rel, s == expected ? "exact" : (sourceOk ? "differs" : "source-differs"), s, "");
        }

        public bool Run()
        {
            var lines = new List<string[]>();
            foreach (var raw in File.ReadAllLines(RecipePath))
                if (raw.Length > 0 && raw[0] != '#') lines.Add(raw.Split('\t'));
            Directory.CreateDirectory(DataOut);
            Directory.CreateDirectory(TempDir);
            var sw = System.Diagnostics.Stopwatch.StartNew();

            var pl = lines.Find(l => l[0] == "palette");
            byte[] palBytes = Entry(pl[1], pl[2], int.Parse(pl[3]));
            if (Sha(palBytes) != pl[4]) Log("WARNING: interfac_x2.drs palette 50500 differs from the reference build (different Expanding Fronts version?)");
            palette = Pal.FromBytes(palBytes);
            string pals = Path.Combine(DeDir, "resources", "_common", "palettes");
            var target = Pal.FromBytes(File.ReadAllBytes(Path.Combine(pals, "original.pal")));
            var playerTarget = Pal.FromBytes(File.ReadAllBytes(Path.Combine(pals, "playercolor_blue.pal")));
            int[] lut = Pal.MappingArray(palette, target);
            int[] playerLut = Pal.MappingArray(palette.Sub(16, 8), playerTarget);

            // Sprites
            var smx = lines.FindAll(l => l[0] == "smx");
            Log(string.Format("Converting {0} sprites (SLP -> SMX)...", smx.Count));
            int done = 0;
            var opts = new ParallelOptions(); opts.MaxDegreeOfParallelism = MaxThreads;
            Parallel.ForEach(smx, opts, l =>
            {
                try
                {
                    byte[] slp = Entry(l[3], "slp", int.Parse(l[4]));
                    bool ok = Sha(slp) == l[5];
                    byte[] data = Sprites.Convert(slp, int.Parse(l[6]), int.Parse(l[7]), int.Parse(l[8]), int.Parse(l[9]),
                        double.Parse(l[10], CultureInfo.InvariantCulture), lut, playerLut);
                    Check(l[1], data, l[2], ok);
                }
                catch (Exception e) { Record(l[1], "error", "", e.Message); }
                int n = Interlocked.Increment(ref done);
                if (n % 250 == 0 || n == smx.Count) Log(string.Format("  sprites {0}/{1}", n, smx.Count));
            });

            // Unit/building sounds
            var wem = lines.FindAll(l => l[0] == "wem");
            Log(string.Format("Converting {0} sounds (WAV -> WEM)...", wem.Count));
            Parallel.ForEach(wem, opts, l =>
            {
                try
                {
                    byte[] wav = Entry(l[3], "wav", int.Parse(l[4]));
                    Check(l[1], Audio.WavToWem(wav), l[2], Sha(wav) == l[5]);
                }
                catch (Exception e) { Record(l[1], "error", "", e.Message); }
            });

            RunMusic(lines, opts);
            RunIcons(lines);
            RunAtlases(lines);

            foreach (var l in lines.FindAll(x => x[0] == "copy"))
            {
                try { Check(l[1], File.ReadAllBytes(Out(l[3])), l[2], true); }
                catch (Exception e) { Record(l[1], "error", "", e.Message); }
            }
            report.Sort(StringComparer.Ordinal);
            File.WriteAllLines(ReportPath, report.ToArray());
            Log(string.Format("Generated {0} files in {1:F0}s: {2} byte-identical to the reference build, {3} rebuilt UI atlases, {4} differ, {5} differ because the source file differs, {6} errors.",
                report.Count, sw.Elapsed.TotalSeconds, Exact, Rebuilt, Differs, SourceDiffers, Errors));
            return Errors == 0;
        }

        string Decode(string source, string name)
        {
            string tool = Path.Combine(ToolsDir, "vgmstream", "vgmstream-cli.exe");
            string dest = Path.Combine(TempDir, name + ".wav");
            var psi = new System.Diagnostics.ProcessStartInfo(tool, "-i -o \"" + dest + "\" \"" + source + "\"");
            psi.UseShellExecute = false; psi.CreateNoWindow = true;
            psi.RedirectStandardOutput = true; psi.RedirectStandardError = true;
            using (var p = System.Diagnostics.Process.Start(psi))
            {
                var o = p.StandardOutput.ReadToEndAsync(); var e = p.StandardError.ReadToEndAsync();
                p.WaitForExit();
                if (p.ExitCode != 0) throw new Exception("vgmstream failed on " + source + ": " + e.Result + o.Result);
            }
            return dest;
        }

        void RunMusic(List<string[]> lines, ParallelOptions opts)
        {
            var cues = lines.FindAll(l => l[0] == "musiccue");
            var slices = lines.FindAll(l => l[0] == "musicslice");
            var sources = lines.FindAll(l => l[0] == "musicsrc");
            Log(string.Format("Decoding music ({0} cues, {1} soundtrack slots)...", cues.Count, slices.Count));
            Parallel.ForEach(cues, opts, l =>
            {
                try
                {
                    string src = Path.Combine(GameDir, l[3].Replace('/', '\\'));
                    bool ok = ShaFile(src) == l[4];
                    string wav = Decode(src, "cue_" + Path.GetFileNameWithoutExtension(l[1]));
                    long off, bytes; int rate, ch, bits;
                    Audio.WavInfo(wav, out off, out bytes, out rate, out ch, out bits);
                    if (bits != 16) throw new InvalidDataException("Decoded music is not 16-bit");
                    using (var f = File.OpenRead(wav)) { f.Position = off; Audio.WriteMusicWem(Out(l[1]), f, bytes, rate, ch); }
                    File.Delete(wav);
                    string s = ShaFile(Out(l[1]));
                    Record(l[1], s == l[2] ? "exact" : (ok ? "differs" : "source-differs"), s, "");
                }
                catch (Exception e) { Record(l[1], "error", "", e.Message); }
            });
            if (slices.Count == 0) return;
            try
            {
                var wavs = new string[sources.Count];
                bool ok = true;
                Parallel.For(0, sources.Count, opts, i =>
                {
                    var l = sources[i];
                    string src = Path.Combine(GameDir, l[2].Replace('/', '\\'));
                    if (ShaFile(src) != l[3]) ok = false;
                    wavs[int.Parse(l[1])] = Decode(src, "shared" + l[1]);
                });
                var offs = new long[wavs.Length]; var frames = new long[wavs.Length];
                long total = 0;
                for (int i = 0; i < wavs.Length; i++)
                {
                    long off, bytes; int rate, ch, bits;
                    Audio.WavInfo(wavs[i], out off, out bytes, out rate, out ch, out bits);
                    if (rate != 44100 || ch != 2 || bits != 16) throw new InvalidDataException("Unexpected soundtrack format " + rate + "/" + ch + "/" + bits);
                    offs[i] = off; frames[i] = bytes / 4; total += frames[i];
                }
                int count = int.Parse(slices[0][4]);
                int stream = 0; long pos = 0; long cursor = 0;
                var files = new FileStream[wavs.Length];
                for (int i = 0; i < wavs.Length; i++) { files[i] = File.OpenRead(wavs[i]); files[i].Position = offs[i]; }
                try
                {
                    slices.Sort((a, b) => int.Parse(a[3]).CompareTo(int.Parse(b[3])));
                    foreach (var l in slices)
                    {
                        int slot = int.Parse(l[3]);
                        long end = total * slot / count;
                        long needed = end - cursor;
                        var parts = new List<KeyValuePair<int, long>>();
                        long n2 = needed; int st = stream; long ps = pos;
                        while (n2 > 0)
                        {
                            long take = Math.Min(n2, frames[st] - ps);
                            parts.Add(new KeyValuePair<int, long>(st, take));
                            n2 -= take; ps += take;
                            if (ps == frames[st]) { st++; ps = 0; }
                        }
                        using (var concat = new ConcatStream(files, parts))
                            Audio.WriteMusicWem(Out(l[1]), concat, needed * 4, 44100, 2);
                        stream = st; pos = ps; cursor = end;
                        string s = ShaFile(Out(l[1]));
                        Record(l[1], s == l[2] ? "exact" : (ok ? "differs" : "source-differs"), s, "");
                    }
                }
                finally { foreach (var f in files) f.Dispose(); }
                foreach (var w in wavs) File.Delete(w);
            }
            catch (Exception e) { foreach (var l in slices) Record(l[1], "error", "", e.Message); }
        }

        // Reads consecutive frame ranges from several decoded WAV streams.
        sealed class ConcatStream : Stream
        {
            readonly FileStream[] files; readonly List<KeyValuePair<int, long>> parts; int part; long left;
            public ConcatStream(FileStream[] files, List<KeyValuePair<int, long>> parts)
            {
                this.files = files; this.parts = parts; part = 0; left = parts.Count > 0 ? parts[0].Value * 4 : 0;
            }
            public override int Read(byte[] buffer, int offset, int count)
            {
                while (part < parts.Count && left == 0) { part++; if (part < parts.Count) left = parts[part].Value * 4; }
                if (part >= parts.Count) return 0;
                int n = files[parts[part].Key].Read(buffer, offset, (int)Math.Min(count, left));
                if (n <= 0) throw new EndOfStreamException();
                left -= n;
                return n;
            }
            public override bool CanRead { get { return true; } }
            public override bool CanSeek { get { return false; } }
            public override bool CanWrite { get { return false; } }
            public override long Length { get { throw new NotSupportedException(); } }
            public override long Position { get { throw new NotSupportedException(); } set { throw new NotSupportedException(); } }
            public override void Flush() { }
            public override long Seek(long o, SeekOrigin s) { throw new NotSupportedException(); }
            public override void SetLength(long v) { throw new NotSupportedException(); }
            public override void Write(byte[] b, int o, int c) { throw new NotSupportedException(); }
        }

        void RunIcons(List<string[]> lines)
        {
            var headers = new Dictionary<string, byte[]>();
            foreach (var l in lines.FindAll(x => x[0] == "ddshdr"))
            {
                var b = new byte[l[2].Length / 2];
                for (int i = 0; i < b.Length; i++) b[i] = byte.Parse(l[2].Substring(2 * i, 2), NumberStyles.HexNumber);
                headers[l[1]] = b;
            }
            var sheets = new Dictionary<string, List<Frame>>();
            var sheetOk = new Dictionary<string, bool>();
            var icons = lines.FindAll(x => x[0] == "icondds" || x[0] == "iconpng");
            Log(string.Format("Rendering {0} interface icons...", icons.Count));
            foreach (var l in icons)
            {
                try
                {
                    bool dds = l[0] == "icondds";
                    int k = dds ? 6 : 5;
                    string archive = l[k], key = archive + ":" + l[k + 1];
                    if (!sheets.ContainsKey(key))
                    {
                        byte[] slp = Entry(archive, "slp", int.Parse(l[k + 1]));
                        sheets[key] = Sprites.LoadSlp(slp, key);
                        sheetOk[key] = Sha(slp) == l[k + 3];
                    }
                    int sw, sh;
                    byte[] rgba = Icons.Render(sheets[key], int.Parse(l[k + 2]), palette, out sw, out sh);
                    iconSource[l[1]] = rgba; iconSize[l[1]] = new int[] { sw, sh };
                    int w = int.Parse(l[dds ? 4 : 3]), h = int.Parse(l[dds ? 5 : 4]);
                    byte[] px = Icons.Resize(rgba, sw, sh, w, h);
                    if (dds)
                    {
                        var hdr = (byte[])headers[l[3]].Clone();
                        var data = new byte[128 + px.Length];
                        Buffer.BlockCopy(hdr, 0, data, 0, 128);
                        Buffer.BlockCopy(px, 0, data, 128, px.Length);
                        Check(l[1], data, l[2], sheetOk[key]);
                    }
                    else
                    {
                        string s = Sha(px);
                        SavePng(Out(l[1]), px, w, h);
                        Record(l[1], s == l[2] ? "exact" : (sheetOk[key] ? "differs" : "source-differs"), s, "RGBA pixels");
                    }
                }
                catch (Exception e) { Record(l[1], "error", "", e.Message); }
            }
        }

        static void SavePng(string path, byte[] rgba, int w, int h)
        {
            using (var bmp = new System.Drawing.Bitmap(w, h, System.Drawing.Imaging.PixelFormat.Format32bppArgb))
            {
                var data = bmp.LockBits(new System.Drawing.Rectangle(0, 0, w, h), System.Drawing.Imaging.ImageLockMode.WriteOnly, System.Drawing.Imaging.PixelFormat.Format32bppArgb);
                var bgra = new byte[w * 4];
                for (int y = 0; y < h; y++)
                {
                    for (int x = 0; x < w; x++)
                    {
                        int o = (y * w + x) * 4;
                        bgra[x * 4] = rgba[o + 2]; bgra[x * 4 + 1] = rgba[o + 1]; bgra[x * 4 + 2] = rgba[o]; bgra[x * 4 + 3] = rgba[o + 3];
                    }
                    System.Runtime.InteropServices.Marshal.Copy(bgra, 0, data.Scan0 + y * data.Stride, w * 4);
                }
                bmp.UnlockBits(data);
                bmp.Save(path, System.Drawing.Imaging.ImageFormat.Png);
            }
        }

        string Texconv(string format, string input, string outDir)
        {
            string tool = Path.Combine(DeDir, "Tools_Builds", "texconv.exe");
            if (!File.Exists(tool)) tool = Path.Combine(ToolsDir, "texconv.exe");
            if (!File.Exists(tool)) throw new FileNotFoundException("texconv.exe not found in AoE2DE\\Tools_Builds");
            Directory.CreateDirectory(outDir);
            var psi = new System.Diagnostics.ProcessStartInfo(tool, "-nologo -f " + format + " -m 1 -y -o \"" + outDir + "\" \"" + input + "\"");
            psi.UseShellExecute = false; psi.CreateNoWindow = true;
            psi.RedirectStandardOutput = true; psi.RedirectStandardError = true;
            using (var p = System.Diagnostics.Process.Start(psi))
            {
                var o = p.StandardOutput.ReadToEndAsync(); var e = p.StandardError.ReadToEndAsync();
                p.WaitForExit();
                string result = Path.Combine(outDir, Path.GetFileName(input));
                if (p.ExitCode != 0 || !File.Exists(result)) throw new Exception("texconv failed: " + o.Result + e.Result);
                return result;
            }
        }

        static byte[] Crop(byte[] px, int w, int[] b)
        {
            int cw = b[2] - b[0], ch = b[3] - b[1];
            var c = new byte[cw * ch * 4];
            for (int y = 0; y < ch; y++) Buffer.BlockCopy(px, ((b[1] + y) * w + b[0]) * 4, c, y * cw * 4, cw * 4);
            return c;
        }

        static void Paste(byte[] px, int w, int h, byte[] src, int[] b)
        {
            int cw = b[2] - b[0], ch = b[3] - b[1];
            if (b[0] < 0 || b[1] < 0 || b[2] > w || b[3] > h || cw <= 0 || ch <= 0) throw new InvalidDataException("Atlas box out of range");
            for (int y = 0; y < ch; y++) Buffer.BlockCopy(src, y * cw * 4, px, ((b[1] + y) * w + b[0]) * 4, cw * 4);
        }

        void RunAtlases(List<string[]> lines)
        {
            var atlases = lines.FindAll(x => x[0] == "atlas");
            if (atlases.Count == 0) return;
            Log(string.Format("Rebuilding {0} DE interface atlases with the SWGB icons (texconv)...", atlases.Count));
            var logic = Materials.Atlases(LogicMaterials);
            var native = Materials.Atlases(Path.Combine(DeDir, "widgetui", "materials.json"));
            var boxes = lines.FindAll(x => x[0] == "atlasbox");
            foreach (var a in atlases)
            {
                try
                {
                    string rel = a[1], name = a[6];
                    int w = int.Parse(a[4]), h = int.Parse(a[5]);
                    string nativePath = Path.Combine(DeDir, rel.Replace('/', '\\'));
                    string work = Path.Combine(TempDir, "atlas-" + Guid.NewGuid().ToString("N"));
                    int nw, nh;
                    byte[] npx = Dds.ReadRgba(Texconv("R8G8B8A8_UNORM", nativePath, work), out nw, out nh);
                    var canvas = new byte[w * h * 4];
                    var nat = new Dictionary<string, AtlasTexture>();
                    foreach (var t in native[name]) nat[t.RefName] = t;
                    int moved = 0;
                    if (nw == w && nh == h) Buffer.BlockCopy(npx, 0, canvas, 0, canvas.Length);
                    foreach (var t in logic[name])
                    {
                        AtlasTexture n;
                        if (!nat.TryGetValue(t.RefName, out n)) continue;
                        int[] db = t.Box(w, h), sb = n.Box(nw, nh);
                        if (nw == w && nh == h && db[0] == sb[0] && db[1] == sb[1] && db[2] == sb[2] && db[3] == sb[3]) continue;
                        if (sb[0] < 0 || sb[1] < 0 || sb[2] > nw || sb[3] > nh) continue;
                        byte[] region = Crop(npx, nw, sb);
                        Paste(canvas, w, h, Icons.Resize(region, sb[2] - sb[0], sb[3] - sb[1], db[2] - db[0], db[3] - db[1]), db);
                        moved++;
                    }
                    int painted = 0;
                    foreach (var b in boxes)
                    {
                        if (b[1] != rel) continue;
                        int[] box = { int.Parse(b[2]), int.Parse(b[3]), int.Parse(b[4]), int.Parse(b[5]) };
                        byte[] icon; int[] size;
                        if (!iconSource.TryGetValue(b[6], out icon)) throw new KeyNotFoundException("Icon not generated: " + b[6]);
                        size = iconSize[b[6]];
                        Paste(canvas, w, h, Icons.Resize(icon, size[0], size[1], box[2] - box[0], box[3] - box[1]), box);
                        painted++;
                    }
                    string input = Path.Combine(work, "in", Path.GetFileName(rel));
                    Directory.CreateDirectory(Path.GetDirectoryName(input));
                    using (var f = new FileStream(input, FileMode.Create))
                    {
                        byte[] hdr = Dds.RgbaHeader(w, h);
                        f.Write(hdr, 0, hdr.Length);
                        f.Write(canvas, 0, canvas.Length);
                    }
                    string encoded = Texconv("BC3_UNORM", input, Path.Combine(work, "out"));
                    string dest = Out(rel);
                    File.Copy(encoded, dest, true);
                    Directory.Delete(work, true);
                    Record(rel, "rebuilt", ShaFile(dest), string.Format("BC3; {0} SWGB icons; {1} native textures relocated from DE {2}x{3} layout", painted, moved, nw, nh));
                }
                catch (Exception e) { Record(a[1], "error", "", e.Message); }
            }
        }
    }
}
