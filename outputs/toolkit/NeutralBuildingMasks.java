import com.imwg.smxworkshop.sprite.*;
import java.nio.file.*;
import java.io.*;
// Add explicit zero damage masks without changing any visible pixels or anchors.
// The input SMX files are the already validated SWGB conversions.
public class NeutralBuildingMasks {
 public static void main(String[] args)throws Exception {
  Palette.loadPalettes();
  int black=0; // Bundled SMX writer stores the numeric damage modifier directly.
  for(String line:Files.readAllLines(Path.of(args[0]))){
   int id=Integer.parseInt(line.trim());
   Path path=Path.of(args[1],"swgb_"+id+".smx");
   Sprite original=SpriteIO.loadFromFile(path.toFile()), patched=new SMXSprite(original);
   for(Sprite.Frame f:patched){
    int w=f.getWidth(0),h=f.getHeight(0);
    f.create(Sprite.DATA_SMUDGE,w,h);f.setAnchor(Sprite.DATA_SMUDGE,f.getAnchorX(0),f.getAnchorY(0));
    for(int y=0;y<h;y++)for(int x=0;x<w;x++)if(f.getPixel(0,x,y)!=Sprite.PIXEL_NULL)f.setPixel(Sprite.DATA_SMUDGE,x,y,black);
   }
   Path dest=Path.of(args[2],path.getFileName().toString());Files.createDirectories(dest.getParent());
   if(!SpriteIO.saveSMXSprite(patched,dest.toString()))throw new Exception("Cannot write "+dest);
   Sprite read=SpriteIO.loadFromFile(dest.toFile());
   if(original.getFrameCount()!=read.getFrameCount())throw new Exception("Frame count changed");
   for(int k=0;k<read.getFrameCount();k++){
    Sprite.Frame a=original.getFrame(k),b=read.getFrame(k);
    for(int t=0;t<3;t++){
     if(a.getWidth(t)!=b.getWidth(t)||a.getHeight(t)!=b.getHeight(t)||a.getAnchorX(t)!=b.getAnchorX(t)||a.getAnchorY(t)!=b.getAnchorY(t))throw new Exception("Layer geometry changed "+id);
     for(int y=0;y<a.getHeight(t);y++)for(int x=0;x<a.getWidth(t);x++)if(a.getPixel(t,x,y)!=b.getPixel(t,x,y))throw new Exception("Pixel changed "+id);
    }
    for(int y=0;y<b.getHeight(0);y++)for(int x=0;x<b.getWidth(0);x++)if(b.getPixel(0,x,y)!=Sprite.PIXEL_NULL&&b.getPixel(Sprite.DATA_SMUDGE,x,y)!=black)throw new Exception("Nonneutral damage mask "+id);
   }
   System.out.println("swgb_"+id+".smx frames="+read.getFrameCount()+" neutral-mask=PASS pixels-and-anchors=UNCHANGED");
  }
 }
}

