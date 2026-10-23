import com.imwg.smxworkshop.sprite.*;
import java.io.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
public class ResourcePaletteAudit {
 public static void main(String[] args)throws Exception{
  Palette.loadPalettes();Palette src=new Palette("../extracted/interfac_x2/50500.bin"),dst=Palette.getPalette(0);
  for(int gid:new int[]{5136,5234,5237}){
   Sprite original=PortSprites.loadSLP(new File("../faction-valid-slp/"+gid+".slp"));
   Sprite converted=SpriteIO.loadFromFile(new File("../faction-roster-converted/swgb_"+gid+".smx"));
   long count=0,sum=0;int max=0;
   for(int i=0;i<original.getFrameCount();i++){
    Sprite.Frame a=original.getFrame(i),b=converted.getFrame(i);
    for(int y=0;y<a.getHeight(0);y++)for(int x=0;x<a.getWidth(0);x++){
     int p=a.getPixel(0,x,y);if(p<0)continue;if(p>=Sprite.PIXEL_PLAYER_START)throw new Exception("Unexpected player pixel");
     int bx=x-a.getAnchorX(0)+b.getAnchorX(0),by=y-a.getAnchorY(0)+b.getAnchorY(0);
     int q=b.getPixel(0,bx,by);if(q<0)throw new Exception("Missing converted pixel");
     int c=src.getColor(p),d=dst.getColor(q);
     int delta=Math.max(Math.abs((c>>16&255)-(d>>16&255)),Math.max(Math.abs((c>>8&255)-(d>>8&255)),Math.abs((c&255)-(d&255))));
     max=Math.max(max,delta);sum+=delta;count++;
    }
   }
   Sprite.Frame a=original.getFrame(0),b=converted.getFrame(0);
   int w=Math.max(a.getWidth(0),b.getWidth(0)),h=Math.max(a.getHeight(0),b.getHeight(0));BufferedImage im=new BufferedImage(w*2+8,h,BufferedImage.TYPE_INT_ARGB);
   for(int j=0;j<2;j++){Sprite.Frame f=j==0?a:b;Palette pal=j==0?src:dst;
    for(int y=0;y<f.getHeight(0);y++)for(int x=0;x<f.getWidth(0);x++){int p=f.getPixel(0,x,y);if(p>=0)im.setRGB(x+j*(w+8),y,0xff000000|pal.getColor(p));}
   }
   ImageIO.write(im,"PNG",new File("../../outputs/resource-palette-"+gid+".png"));
   System.out.println(gid+" pixels="+count+" maximum_channel_error="+max+" mean_max_channel_error="+((double)sum/count));
  }
 }
}
