#pragma once
inline int factionLanguageName(bool tech,int civ,int id){
 return (tech?4000000:1000000+civ*1000000)+(id/1000)*100000+id%1000;
}
