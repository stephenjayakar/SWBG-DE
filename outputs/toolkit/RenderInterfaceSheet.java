import com.imwg.smxworkshop.sprite.*;
import java.io.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
// Render original indexed interface frames, preserving transparency and pixels.
public class RenderInterfaceSheet {
 public static void main(String[] args)throws Exception {
  Palette palette=new Palette(args[2]);
  Sprite sheet=PortSprites.loadSLP(new File(args[0]));
  File out=new File(args[1]);out.mkdirs();
  for(int k=0;k<sheet.getFrameCount();k++){
   Sprite.Frame f=sheet.getFrame(k);
   BufferedImage im=new BufferedImage(f.getWidth(0),f.getHeight(0),BufferedImage.TYPE_INT_ARGB);
   for(int y=0;y<im.getHeight();y++)for(int x=0;x<im.getWidth();x++){
    int p=f.getPixel(0,x,y);if(p==Sprite.PIXEL_NULL)continue;
    if(p>=Sprite.PIXEL_PLAYER_START)p=p-Sprite.PIXEL_PLAYER_START+16;
    im.setRGB(x,y,0xff000000|palette.getColor(p));
   }
   ImageIO.write(im,"PNG",new File(out,k+".png"));
  }
 }
}
