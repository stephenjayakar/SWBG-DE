import com.imwg.smxworkshop.sprite.*;
import java.io.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
public class PortSprites {
 // SWGB artwork has its damage/death appearance already painted into sprites.
 // Always encode neutral DE damage values, including effects and corpses.
 static void neutralDamage(Sprite sprite){
  for(Sprite.Frame f:sprite){
   int w=f.getWidth(0),h=f.getHeight(0);
   if(w==0||h==0)continue;
   f.create(Sprite.DATA_SMUDGE,w,h);
   f.setAnchor(Sprite.DATA_SMUDGE,f.getAnchorX(0),f.getAnchorY(0));
   for(int y=0;y<h;y++)for(int x=0;x<w;x++)
    if(f.getPixel(0,x,y)!=Sprite.PIXEL_NULL)f.setPixel(Sprite.DATA_SMUDGE,x,y,0);
  }
 }
 static int u32(RandomAccessFile f)throws Exception{return Integer.reverseBytes(f.readInt());}
 static int u16(RandomAccessFile f)throws Exception{return Short.toUnsignedInt(Short.reverseBytes(f.readShort()));}
 static Sprite loadSLP(File input)throws Exception{
  RandomAccessFile f=new RandomAccessFile(input,"r");f.seek(4);int count=u32(f);Sprite s=new SMXSprite();s.setMemo("SWGB");
  for(int i=0;i<count;i++){
   f.seek(32+32*i);int commands=u32(f),outline=u32(f);u32(f);u32(f);int w=u32(f),h=u32(f),ax=u32(f),ay=u32(f);
   Sprite.Frame frame=s.createFrame();frame.create(w,h);frame.setAnchor(Sprite.DATA_IMAGE,ax,ay);frame.setAnchor(Sprite.DATA_SHADOW,ax,ay);frame.setAnchor(Sprite.DATA_OUTLINE,ax,ay);s.insertFrame(i,frame);
   for(int y=0;y<h;y++){
    f.seek(outline+4*y);int x=u16(f),right=u16(f);if(x==32768||right==32768)continue;
    f.seek(commands+4*y);int addr=u32(f);f.seek(addr);
    while(true){int b=f.readUnsignedByte(),op=b&15,n=b>>4,t=0,p=-1;
     if(op==15)break;
     if((b&3)==0){n=b>>2;for(int j=0;j<n;j++)frame.setPixel(0,x++,y,f.readUnsignedByte());continue;}
     if((b&3)==1){x+=b>>2;continue;}
     if(op==2){n=((b&240)<<4)+f.readUnsignedByte();for(int j=0;j<n;j++)frame.setPixel(0,x++,y,f.readUnsignedByte());continue;}
     if(op==3){x+=((b&240)<<4)+f.readUnsignedByte();continue;}
     if(op==6){if(n==0)n=f.readUnsignedByte();for(int j=0;j<n;j++)frame.setPixel(0,x++,y,Sprite.PIXEL_PLAYER_START+f.readUnsignedByte());continue;}
     if(op==7||op==10||op==11){if(n==0)n=f.readUnsignedByte();if(op==11){t=1;p=128;}else p=f.readUnsignedByte()+(op==10?Sprite.PIXEL_PLAYER_START:0);}
     else if(b==78||b==94){t=2;p=0;n=b==78?1:f.readUnsignedByte();}
     else if(b==110||b==126){n=b==110?1:f.readUnsignedByte();x+=n;continue;}
     else throw new Exception("Unsupported SLP opcode "+b+" "+input);
     for(int j=0;j<n;j++)frame.setPixel(t,x++,y,p);
    }
   }
  }f.close();return s;
 }
 public static void main(String[] args)throws Exception {
  Palette.loadPalettes();
  Palette source=new Palette(args[2]), target=Palette.getPalette(0);
  Palette playerSource=new Palette(source,16,8), playerTarget=Palette.getPlayerPalette(Sprite.PLAYER_PALETTE_DE,0);
  File out=new File(args[1]);out.mkdirs();
  java.util.Map<Integer,int[]> metadata=new java.util.HashMap<>();
  for(String line:java.nio.file.Files.readAllLines(java.nio.file.Path.of("../../outputs/ef-graphics.tsv"))){String[] v=line.split("\t",-1);if(!v[0].equals("id"))metadata.put(Integer.parseInt(v[0]),new int[]{Integer.parseInt(v[4]),Integer.parseInt(v[5]),Integer.parseInt(v[7])});}
  int failures=0;
  for(File input:new File(args[0]).listFiles((d,n)->n.endsWith(".slp"))){
   try {
   Sprite s=loadSLP(input);if(s==null||s.getFrameCount()==0)throw new Exception("Empty "+input);
   int graphicId=Integer.parseInt(input.getName().replace(".slp",""));
   if(java.util.Set.of(10611,10612,10613,10614,10615,16291,16292).contains(graphicId)){
    // These source files contain nonstandard player shades 8..15. Preserve
    // their blue-player palette appearance as fixed paint (a small compromise).
    int repaired=0;
    for(Sprite.Frame f:s)for(int y=0;y<f.getHeight(0);y++)for(int x=0;x<f.getWidth(0);x++){
     int p=f.getPixel(0,x,y)-Sprite.PIXEL_PLAYER_START;
     if(p>=8){if(p>15)throw new Exception("Unexpected extended player shade "+p);f.setPixel(0,x,y,16+p);repaired++;}
    }
    System.out.println("REPAIR "+graphicId+" fixed-paint pixels="+repaired+" source player shades 8..15");
   }
   int[] meta=metadata.get(Integer.parseInt(input.getName().replace(".slp","")));
   Sprite converted=new SMXSprite();
   boolean empty=true;
   for(Sprite.Frame f:s)for(int t=0;t<3;t++)for(int y=0;y<f.getHeight(t)&&empty;y++)for(int x=0;x<f.getWidth(t);x++)if(f.getPixel(t,x,y)!=-1){empty=false;break;}
   if(empty){
    for(int k=0;k<meta[0]*meta[1];k++)converted.insertFrame(k,converted.createFrame(s.getFrame(0)));
    System.out.println("EMPTY "+graphicId+" transparent placeholder expanded to metadata layout");
   }else if(meta[1]==8||meta[1]==16){
    int angles=meta[1],half=angles/2;
    boolean mirrored=meta[2]!=0;
    int sourceFrames=meta[0];
    if(graphicId==5582&&s.getFrameCount()==5&&mirrored&&angles==8){sourceFrames=1;System.out.println("REPAIR 5582 static directional frames repeated for declared animation duration");}
    if(s.getFrameCount()!=sourceFrames*(mirrored?half+1:angles))throw new Exception("Direction/frame count mismatch: "+input);
    // Source starts south and advances west; DE starts east and advances south.
    for(int angle=0;angle<angles;angle++){
     int direction=(angle-angles/4+angles)%angles;
     int group=mirrored?(direction<=half?direction:angles-direction):direction;
     for(int k=0;k<meta[0];k++){
      Sprite.Frame f=converted.createFrame(s.getFrame(group*sourceFrames+k%sourceFrames));
      if(mirrored&&direction>half)f.flip(Sprite.FLIP_HORIZONTAL);
      converted.insertFrame(converted.getFrameCount(),f);
     }
    }
   }else if(meta[1]==1||meta[1]==3||meta[1]==5){
    if(s.getFrameCount()<meta[0]*meta[1])throw new Exception("Variation/stage count mismatch: "+input);
    converted=new SMXSprite(s);
   }else if(meta[2]==0&&(meta[1]==2||meta[1]==6||meta[1]==10||meta[1]==11||meta[1]==12||meta[1]==22||meta[1]==24)){
    // Resource piles and trees store independent variants, not facings.
    if(s.getFrameCount()<meta[0]*meta[1])throw new Exception("Resource variation count mismatch: "+input);
    converted=new SMXSprite(s);
   }else throw new Exception("Unsupported angle count: "+meta[1]+" "+input);
   for(Sprite.Frame f:converted){
    f.changePixelsByPalette(source,target,false);f.changePixelsByPalette(playerSource,playerTarget,true);f.setPalette(0);
    double scale=args.length>3?Double.parseDouble(args[3]):1.0;
    if(input.getName().equals("13106.slp")||input.getName().equals("11805.slp"))scale*=3.0;
    f.scale(scale);
   }
   converted.setPlayerMode(Sprite.PLAYER_PALETTE_DE);converted.setMemo("SWGB DE full directions");
   neutralDamage(converted);
   File dest=new File(out,"swgb_"+input.getName().replace(".slp",".smx"));
   if(!SpriteIO.saveSMXSprite(converted,dest.toString()))throw new Exception("Save failed");
   Sprite read=SpriteIO.loadFromFile(dest);if(read.getFrameCount()!=converted.getFrameCount())throw new Exception("Frame mismatch");
   for(Sprite.Frame f:read)for(int y=0;y<f.getHeight(0);y++)for(int x=0;x<f.getWidth(0);x++)
    if(f.getPixel(0,x,y)!=Sprite.PIXEL_NULL&&f.getPixel(Sprite.DATA_SMUDGE,x,y)!=0)
     throw new Exception("Nonneutral damage modifier "+dest);
   for(int k=0;k<read.getFrameCount();k++)for(int t=0;t<3;t++){
    Sprite.Frame a=converted.getFrame(k),b=read.getFrame(k);
    if(a.getWidth(t)==b.getWidth(t)&&a.getHeight(t)==b.getHeight(t)&&a.getAnchorX(t)==b.getAnchorX(t)&&a.getAnchorY(t)==b.getAnchorY(t)){
     for(int y=0;y<a.getHeight(t);y++)for(int x=0;x<a.getWidth(t);x++)if(a.getPixel(t,x,y)!=b.getPixel(t,x,y))throw new Exception("Pixel mismatch "+dest);
     continue;
    }
    java.util.Map<Long,Integer> pa=new java.util.HashMap<>(),pb=new java.util.HashMap<>();
    for(int y=0;y<a.getHeight(t);y++)for(int x=0;x<a.getWidth(t);x++)if(a.getPixel(t,x,y)!=-1)
     pa.put(((long)(x-a.getAnchorX(t))<<32)|((y-a.getAnchorY(t))&0xffffffffL),a.getPixel(t,x,y));
    for(int y=0;y<b.getHeight(t);y++)for(int x=0;x<b.getWidth(t);x++)if(b.getPixel(t,x,y)!=-1)
     pb.put(((long)(x-b.getAnchorX(t))<<32)|((y-b.getAnchorY(t))&0xffffffffL),b.getPixel(t,x,y));
    if(!pa.equals(pb))throw new Exception("Rendered pixel/anchor mismatch "+dest);

   }
   Sprite.Frame f=read.getFrame(0);BufferedImage im=new BufferedImage(Math.max(1,f.getWidth(0)),Math.max(1,f.getHeight(0)),BufferedImage.TYPE_INT_ARGB);
   for(int y=0;y<im.getHeight();y++)for(int x=0;x<im.getWidth();x++){int p=x<f.getWidth(0)&&y<f.getHeight(0)?f.getPixel(0,x,y):-1;if(p!=-1)im.setRGB(x,y,0xff000000|(p>=Sprite.PIXEL_PLAYER_START?playerTarget.getColor(p-Sprite.PIXEL_PLAYER_START):target.getColor(p)));}
   ImageIO.write(im,"PNG",new File(out,dest.getName()+".png"));
   System.out.println(dest.getName()+" frames="+read.getFrameCount()+" roundtrip=PASS");
   } catch(Exception e) { failures++;System.err.println("FAILED "+input.getName()+": "+e); }
  }
  if(failures>0)throw new Exception(failures+" sprites failed; see FAILED records");
 }
}
