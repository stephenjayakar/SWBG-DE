import com.imwg.smxworkshop.sprite.*;
import java.nio.file.*;
// Independent library decoder checks palette indices and all render geometry.
public class VerifyNeutralSprites {
 public static void main(String[] args)throws Exception {
  Palette.loadPalettes();int files=0;long pixels=0;
  for(String line:Files.readAllLines(Path.of(args[0]))){
   String[] r=line.split("\t");
   Sprite a=SpriteIO.loadFromFile(Path.of(r[0]).toFile());
   Sprite b=r[0].equals(r[1])?a:SpriteIO.loadFromFile(Path.of(r[1]).toFile());
   if(a.getFrameCount()!=b.getFrameCount()||a.getPlayerMode()!=b.getPlayerMode())throw new Exception("Sprite metadata "+line);
   for(int k=0;k<a.getFrameCount();k++){
    Sprite.Frame x=a.getFrame(k),y=b.getFrame(k);
    if(x.getPalette()!=y.getPalette())throw new Exception("Palette "+line);
    for(int t=0;t<3;t++){
     if(x.getWidth(t)!=y.getWidth(t)||x.getHeight(t)!=y.getHeight(t)||x.getAnchorX(t)!=y.getAnchorX(t)||x.getAnchorY(t)!=y.getAnchorY(t))throw new Exception("Geometry "+line);
     for(int j=0;j<x.getHeight(t);j++)for(int i=0;i<x.getWidth(t);i++){
      int pixel=x.getPixel(t,i,j);
      if(pixel!=y.getPixel(t,i,j))throw new Exception("Pixel "+line+" frame="+k+" xy="+i+","+j);
      if(t==0&&pixel!=Sprite.PIXEL_NULL){
       if(y.getWidth(Sprite.DATA_SMUDGE)!=y.getWidth(0)||y.getHeight(Sprite.DATA_SMUDGE)!=y.getHeight(0)
          ||y.getAnchorX(Sprite.DATA_SMUDGE)!=y.getAnchorX(0)||y.getAnchorY(Sprite.DATA_SMUDGE)!=y.getAnchorY(0)
          ||y.getPixel(Sprite.DATA_SMUDGE,i,j)!=0)throw new Exception("Damage mask "+line);
       pixels++;
      }
     }
    }
   }
   files++;if(files%50==0)System.out.println("verified="+files+" visible-pixels="+pixels);
  }
  System.out.println("PASS files="+files+" visible-pixels="+pixels);
  if(args.length>1)Files.writeString(Path.of(args[1]),"PASS files="+files+" visible-pixels="+pixels+"\n");
 }
}
