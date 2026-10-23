// Raw-file adapter: Python performs RFC1951 compression outside the DAT parser.
#include "genie/file/Compressor.h"
namespace genie {
Compressor::Compressor() {}
Compressor::Compressor(ISerializable* obj):obj_(obj) {}
Compressor::~Compressor() {}
void Compressor::beginCompression() {}
void Compressor::endCompression() {}
void Compressor::decompress(std::istream& source,std::ostream& sink) { sink<<source.rdbuf(); }
}
