/*

mysterious_heap

...
...
...
...
...
...





*/

#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <vector>
#include <map>

#include "crc32.h"
#include "payload_chunk.pb.h"

#define POOL_FLAG_IS_FREE 0x0001
#define POOL_FLAG_IS_INTERESTING 0x0004
#define POOL_FLAG_IS_CORRUPTED 0x0008

#define HINT_PATH "hint"
#define DECODED_DATA_PATH "decoded_data"

struct Pool_Node
{
    Pool_Node *prev;
    Pool_Node *next;
    size_t data_size;
    int64_t flags;
    // then data
};

struct Interesting_Pool_Node
{
    int64_t hint_key;
    int64_t hint_length;
};

struct SubHeader
{
    uint64_t key;
    uint64_t data_length;
};

struct PayloadChunkHeader
{
    size_t index;      // index of a chunk (number)
    uint64_t key;      // Encryption key for some other chunk (see below)!
    uint64_t crc32;    // Hash of a decrypted chunk
    size_t chunk_size; // Size of a chunk in bytes.
};

struct ChunkData
{
    PayloadChunkHeader header;
    std::vector<uint8_t> encrypted_data;
};

void xor_encdec_8(void *data, size_t data_size, uint64_t key)
{
    // ----------------------------------------------
    // Implement XOR encoding/decoding.
    // This is very simple.
    // Key is uint64 - 8 bytes.
    // Each 8 bytes of `data` must be XOR'ed with the Key.
    //
    // Please note! `data_size` may be not divisible by 8.
    // In that case, cast the key to uint8_t XOR all the
    // remaining bytes with it.
    // ----------------------------------------------
    // A good test for `xor_encdec_8` is to apply it twice
    // Since, well, as you know, a xor k xor k = a
    uint64_t *data_8 = (uint64_t *)data;
    for (size_t i = 0; i < data_size / sizeof(key); ++i)
    {
        data_8[i] = data_8[i] ^ key;
    }

    uint8_t *data_1 = (uint8_t *)(data_8 + data_size / sizeof(key));
    uint8_t key_1 = (uint8_t)key & 0xFF;
    for (size_t i = 0; i < data_size % sizeof(key); ++i)
    {
        data_1[i] = data_1[i] ^ key_1;
    }
}

size_t read_file(const char *fname, void **dst)
{
    FILE *f = fopen(fname, "rb");
    if (NULL == f)
    {
        fprintf(stderr, "File not found: %s\n", fname);
        exit(1);
    }
    fseek(f, 0L, SEEK_END);
    size_t sz = ftell(f);
    fseek(f, 0L, SEEK_SET);
    *dst = malloc(sz);
    sz = fread(*dst, 1, sz + 1, f);
    assert(feof(f));
    fclose(f);
    return sz;
}

/// Call this function to load the heap file.
size_t mysterious_heap_load(uint8_t **memory, const char *fname)
{
    size_t memory_size = read_file(fname, (void **)memory);
    printf("Computing heap hash.\n");
    uint32_t hash = crc32(*memory, memory_size);
    printf("crc32 = %u\n", hash);

    uint8_t *mem = *memory;
    Pool_Node *p = (Pool_Node *)(mem);
    while (NULL != p)
    {
        if (p->next)
        {
            p->next = (Pool_Node *)((uint8_t *)p->next + (uintptr_t)(*memory - 1));
        }
        if (p->prev)
        {
            p->prev = (Pool_Node *)((uint8_t *)p->prev + (uintptr_t)(*memory - 1));
        }
        p = p->next;
    }
    return memory_size;
}

void get_hint1(uint8_t *memory, size_t memory_size)
{
    Pool_Node *p = (Pool_Node *)(memory);
    FILE *output_file = fopen(HINT_PATH, "wb");
    if (!output_file)
    {
        fprintf(stderr, "Error: Cannot create output file\n");
        return;
    }

    while (p != NULL)

    {

        if (p->flags & POOL_FLAG_IS_INTERESTING)
        {
            Interesting_Pool_Node *inter_p = (Interesting_Pool_Node *)(p + 1);
            uint8_t *hint = (uint8_t *)inter_p + sizeof(Interesting_Pool_Node);
            xor_encdec_8(hint, inter_p->hint_length, inter_p->hint_key);
            fprintf(stderr, "key=%lld length=%lld\n", inter_p->hint_key, inter_p->hint_length);
            fprintf(stderr, "%s\n", hint);

            uint8_t *payload = hint + inter_p->hint_length;
            SubHeader *sub_header = (SubHeader *)payload;

            fprintf(stderr, "SubHeader key=%llu data_length=%llu\n", sub_header->key, sub_header->data_length);

            uint8_t *data = (uint8_t *)sub_header + sizeof(SubHeader);

            uint8_t *data_copy = (uint8_t *)malloc(sub_header->data_length);
            memcpy(data_copy, data, sub_header->data_length);
            xor_encdec_8(data_copy, sub_header->data_length, sub_header->key);

            fwrite(data_copy, 1, sub_header->data_length, output_file);

            fprintf(stderr, "Extracted %llu bytes of data\n", sub_header->data_length);

            free(data_copy);
        }
        p = p->next;
    }

    fclose(output_file);
    std::cout << "Data extraction complete. Saved to " << HINT_PATH << std::endl;
}

NextHint parse_hint_file(const std::string hint_path)
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    std::cout << "\nParsing hint file '" << hint_path << "'..." << std::endl;
    std::ifstream hint_file(hint_path, std::ios::binary);
    if (!hint_file.is_open())
    {
        std::cerr << "Error: Cannot open hint file" << std::endl;
        return NextHint();
    }

    std::string hint_data((std::istreambuf_iterator<char>(hint_file)), std::istreambuf_iterator<char>());
    hint_file.close();

    std::string start_marker_str = "file\n```";
    size_t start_marker = hint_data.find(start_marker_str);
    if (start_marker == std::string::npos)
    {
        std::cerr << "Error: Cannot find start marker '" << start_marker_str << "'" << std::endl;
        return NextHint();
    }

    std::string end_marker_str = "syntax";
    size_t end_marker = hint_data.find(end_marker_str);
    if (end_marker == std::string::npos)
    {
        std::cerr << "Error: Cannot find end marker '" << end_marker_str << "'" << std::endl;
        return NextHint();
    }

    size_t protobuf_start = hint_data.find('\n', start_marker) + 1;
    std::string protobuf_data = hint_data.substr(protobuf_start, end_marker - protobuf_start);

    std::cout << "Protobuf start offset: " << protobuf_start << std::endl;
    std::cout << "Protobuf end offset: " << end_marker << std::endl;
    std::cout << "Protobuf data size: " << protobuf_data.size() << " bytes" << std::endl;

    NextHint next_hint;
    if (!next_hint.ParseFromString(protobuf_data))
    {
        std::cerr << "Error: Failed to parse protobuf message" << std::endl;
        return NextHint();
    }

    std::cout << "Successfully parsed protobuf!" << std::endl;
    std::cout << "Number of chunks: " << next_hint.chunks_info_size() << std::endl;

    return next_hint;
}

std::map<size_t, size_t> create_key_to_chunk_mapping(const NextHint &next_hint)
{
    std::cout << "\nChunk ID -> Key ID Mapping:" << std::endl;
    std::map<size_t, size_t> chunk_to_key_mapping;
    for (int i = 0; i < next_hint.chunks_info_size(); ++i)
    {
        const PayloadChunk &chunk = next_hint.chunks_info(i);
        chunk_to_key_mapping[chunk.key_id()] = chunk.chunk_id();
        std::cout << "chunk_id=" << std::setw(2) << chunk.chunk_id()
                  << " encrypts with key from chunk_id=" << std::setw(2) << chunk.key_id()
                  << std::endl;
    }

    return chunk_to_key_mapping;
}

std::vector<ChunkData> extract_encrypted_chunks(uint8_t *memory)
{
    std::cout << "\nSearch for payload chunks with flag 0x0008..." << std::endl;

    std::vector<ChunkData> chunks;
    Pool_Node *node = reinterpret_cast<Pool_Node *>(memory);
    while (node != nullptr)
    {
        if (node->flags & POOL_FLAG_IS_CORRUPTED)
        {
            PayloadChunkHeader *payload_header = reinterpret_cast<PayloadChunkHeader *>(node + 1);
            uint8_t *payload_data = reinterpret_cast<uint8_t *>(payload_header + 1);

            ChunkData chunk;
            chunk.header = *payload_header;

            chunk.encrypted_data.assign(payload_data, payload_data + payload_header->chunk_size);

            chunks.push_back(std::move(chunk));

            std::cout << "Found chunk index=" << payload_header->index
                      << ", key=" << payload_header->key
                      << ", crc32=" << payload_header->crc32
                      << ", size=" << payload_header->chunk_size << std::endl;
        }

        node = node->next;
    }

    std::cout << "Total chunks found: " << chunks.size() << std::endl;
    return chunks;
}

std::vector<std::vector<uint8_t>> decrypt_and_verify_chunks(
    const std::vector<ChunkData> &chunks,
    const std::map<size_t, size_t> &chunk_to_key_mapping)
{
    std::map<size_t, uint64_t> index_to_key;
    for (const auto &chunk : chunks)
    {
        index_to_key[chunk.header.index] = chunk.header.key;
    }

    std::cout << "\nDecrypting chunks..." << std::endl;
    std::vector<std::vector<uint8_t>> decrypted_chunks(chunks.size());
    for (const auto &chunk : chunks)
    {
        size_t chunk_id = chunk.header.index;

        auto key_iter = chunk_to_key_mapping.find(chunk_id);
        if (key_iter == chunk_to_key_mapping.end())
        {
            std::cerr << "Error: No mapping found for chunk_id=" << chunk_id << std::endl;
            continue;
        }

        size_t key_chunk_id = key_iter->second;
        auto key_value_iter = index_to_key.find(key_chunk_id);
        if (key_value_iter == index_to_key.end())
        {
            std::cerr << "Error: Key chunk " << key_chunk_id << " not found for chunk " << chunk_id << std::endl;
            continue;
        }

        uint64_t decryption_key = key_value_iter->second;

        std::cout << "Chunk " << chunk_id
                  << ": using key from chunk " << key_chunk_id
                  << " (key=" << decryption_key << ")"
                  << std::endl;

        std::vector<uint8_t> decrypted_data(chunk.encrypted_data.begin(), chunk.encrypted_data.end());
        xor_encdec_8(decrypted_data.data(), decrypted_data.size(), decryption_key);
        uint32_t computed_crc = crc32(decrypted_data.data(), decrypted_data.size());
        if (computed_crc != chunk.header.crc32)
        {
            std::cerr << "Chunk " << chunk_id << " CRC32 mismatch! "
                      << "Expected=" << chunk.header.crc32
                      << ", Got=" << computed_crc
                      << std::endl;

            decrypted_chunks[chunk_id].clear();
        }

        std::cout << "Chunk " << chunk_id << " decrypted successfully (CRC32 verified)" << std::endl;
        decrypted_chunks[chunk_id] = std::move(decrypted_data);
    }

    return decrypted_chunks;
}

std::vector<uint8_t> assemble_final_data(
    const std::vector<std::vector<uint8_t>> &decrypted_chunks,
    const std::vector<ChunkData> &chunks)
{
    std::cout << "\nAssembling final data..." << std::endl;

    std::unordered_map<size_t, const ChunkData *> chunk_map;
    size_t total_size = 0;
    for (const ChunkData &chunk : chunks)
    {
        chunk_map[chunk.header.index] = &chunk;
        total_size += chunk.header.chunk_size;
    }

    std::vector<uint8_t> final_data;
    final_data.reserve(total_size);
    for (size_t i = 0; i < decrypted_chunks.size(); ++i)
    {
        const std::vector<uint8_t> &chunk_data = decrypted_chunks[i];

        if (chunk_data.empty())
        {
            std::cerr << "Warning: Chunk " << i << " is missing or invalid" << std::endl;
            continue;
        }

        auto it = chunk_map.find(i);
        if (it != chunk_map.end())
        {
            const ChunkData *matching_chunk = it->second;
            final_data.insert(final_data.end(),
                              chunk_data.begin(),
                              chunk_data.begin() + matching_chunk->header.chunk_size);
        }
    }

    return final_data;
}

void save_final_data(const std::vector<uint8_t> &final_data, const std::string save_path)
{
    uint32_t final_crc = crc32(final_data.data(), final_data.size());
    std::cout << "\nSaving final data to '" << save_path << "'..." << std::endl;
    std::cout
        << "\nFinal data size: " << final_data.size() << " bytes" << std::endl;
    std::cout << "Final CRC32: " << final_crc << std::endl;
    std::cout << "To finalize the file run next command: python ../finalize_the_file.py --hash " << final_crc << " --filepath " << save_path << std::endl;

    std::ofstream output_file(save_path, std::ios::binary);
    if (!output_file)
    {
        std::cerr << "Error: Cannot create output file" << std::endl;
        return;
    }

    output_file.write(reinterpret_cast<const char *>(final_data.data()), final_data.size());
}

void get_hint2(uint8_t *memory)
{
    NextHint next_hint = parse_hint_file(HINT_PATH);
    if (next_hint.chunks_info_size() == 0)
    {
        std::cerr << "Failed to parse hint file or no chunks available" << std::endl;
        return;
    }

    std::map<size_t, size_t> chunk_to_key_mapping = create_key_to_chunk_mapping(next_hint);
    if (chunk_to_key_mapping.empty())
    {
        std::cerr << "Failed to create chunk mapping" << std::endl;
        return;
    }

    std::vector<ChunkData> chunks = extract_encrypted_chunks(memory);
    if (chunks.empty())
    {
        std::cerr << "No chunks found" << std::endl;
        return;
    }

    std::vector<std::vector<uint8_t>> decrypted_chunks = decrypt_and_verify_chunks(chunks, chunk_to_key_mapping);
    std::vector<uint8_t> final_data = assemble_final_data(decrypted_chunks, chunks);
    save_final_data(final_data, DECODED_DATA_PATH);

    google::protobuf::ShutdownProtobufLibrary();
}

int main()
{
    const char *fname = "../mysterious_heap";
    uint8_t *memory = NULL;
    size_t memory_size = mysterious_heap_load(&memory, fname);
    get_hint1(memory, memory_size);
    get_hint2(memory);
    free(memory);
    return 0;
}