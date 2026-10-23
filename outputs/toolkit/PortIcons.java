import com.imwg.smxworkshop.sprite.*;
import java.io.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.nio.file.*;
import java.util.*;
public class PortIcons {
 public static void main(String[] args)throws Exception {
  Palette source=new Palette(args[2]);
  Map<Integer,Sprite> sheets=new HashMap<>();
  File out=new File(args[1]);out.mkdirs();int count=0;
  for(String line:Files.readAllLines(Path.of(args[0]))){
   if(line.startsWith("civ\t"))continue;
   String[] r=line.split("\t");int slp=Integer.parseInt(r[3]),frame=Integer.parseInt(r[4]);
   if(!sheets.containsKey(slp))sheets.put(slp,PortSprites.loadSLP(new File("../faction-icon-slp/"+slp+".slp")));
   Sprite s=sheets.get(slp);
   if(frame<0||frame>=s.getFrameCount())throw new Exception("Missing icon frame "+line);
   Sprite.Frame f=s.getFrame(frame);
   BufferedImage im=new BufferedImage(f.getWidth(0),f.getHeight(0),BufferedImage.TYPE_INT_ARGB);
   for(int y=0;y<im.getHeight();y++)for(int x=0;x<im.getWidth();x++){
    int p=f.getPixel(0,x,y);if(p==-1)continue;
    if(p>=Sprite.PIXEL_PLAYER_START)p=p-Sprite.PIXEL_PLAYER_START+16;
    im.setRGB(x,y,0xff000000|source.getColor(p));
   }
   File dest=new File(out,r[0]+"_"+r[1]+"_"+r[2]+".png");ImageIO.write(im,"PNG",dest);
   BufferedImage read=ImageIO.read(dest);
   if(read.getWidth()!=im.getWidth()||read.getHeight()!=im.getHeight())throw new Exception("Icon size mismatch");
   for(int y=0;y<im.getHeight();y++)for(int x=0;x<im.getWidth();x++)if(read.getRGB(x,y)!=im.getRGB(x,y))throw new Exception("Icon pixel mismatch");
   count++;
  }
  System.out.println(count+" source icon bindings rendered and PNG pixels verified");
 }
}
