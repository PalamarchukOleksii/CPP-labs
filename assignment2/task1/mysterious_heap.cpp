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

using namespace std;

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
    uint8_t *encrypted_data;

    ChunkData() : encrypted_data(nullptr) {}
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
    FILE *output_file = fopen("../hint", "wb");
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
    printf("Data extraction complete. Saved to ../hint\n");
}

map<size_t, size_t> parse_hint_and_create_mapping()
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    ifstream hint_file("../hint", ios::binary);
    if (!hint_file)
    {
        hint_file.open("hint", ios::binary);
        if (!hint_file)
        {
            fprintf(stderr, "Error: Cannot open hint file\n");
            return map<size_t, size_t>();
        }
    }

    string hint_data((istreambuf_iterator<char>(hint_file)),
                     istreambuf_iterator<char>());
    hint_file.close();

    size_t schema_pos = hint_data.find("syntax = ");

    if (schema_pos == string::npos)
    {
        fprintf(stderr, "Error: Cannot find schema marker\n");
        return map<size_t, size_t>();
    }

    string protobuf_data = hint_data.substr(0, schema_pos);
    printf("Protobuf data size: %zu bytes\n", protobuf_data.size());

    NextHint next_hint;
    if (!next_hint.ParseFromString(protobuf_data))
    {
        fprintf(stderr, "Error: Failed to parse protobuf message\n");
        return map<size_t, size_t>();
    }

    printf("Successfully parsed protobuf!\n");
    printf("Number of chunks: %d\n", next_hint.chunks_info_size());
    printf("Hint message: %s\n", next_hint.hint_message().c_str());

    printf("\nChunk ID -> Key ID Mapping:\n");
    printf("--------------------------------------------------\n");

    map<size_t, size_t> chunk_to_key_mapping;

    for (int i = 0; i < next_hint.chunks_info_size(); i++)
    {
        const PayloadChunk &chunk = next_hint.chunks_info(i);
        chunk_to_key_mapping[chunk.key_id()] = chunk.chunk_id();
        printf("  chunk_id=%3lld encrypts with key from chunk_id=%3lld\n",
               (long long)chunk.chunk_id(), (long long)chunk.key_id());
    }

    return chunk_to_key_mapping;
}

vector<ChunkData> extract_corrupted_chunks(uint8_t *memory)
{
    printf("\nNext: Search for payload chunks with flag 0x0008...\n\n");

    vector<ChunkData> chunks;
    Pool_Node *p = (Pool_Node *)(memory);

    while (p != NULL)
    {
        if (p->flags & POOL_FLAG_IS_CORRUPTED)
        {
            PayloadChunkHeader *payload_chunk_p = (PayloadChunkHeader *)(p + 1);
            uint8_t *payload_chunk = (uint8_t *)payload_chunk_p + sizeof(PayloadChunkHeader);

            ChunkData chunk;
            chunk.header = *payload_chunk_p;

            chunk.encrypted_data = (uint8_t *)malloc(payload_chunk_p->chunk_size);
            memcpy(chunk.encrypted_data, payload_chunk, payload_chunk_p->chunk_size);

            chunks.push_back(chunk);

            printf("Found chunk index=%zu, key=%llu, crc32=%llu, size=%zu\n",
                   payload_chunk_p->index, payload_chunk_p->key,
                   payload_chunk_p->crc32, payload_chunk_p->chunk_size);
        }
        p = p->next;
    }

    printf("Total chunks found: %zu\n\n", chunks.size());
    return chunks;
}

vector<uint8_t *> decrypt_and_verify_chunks(
    const vector<ChunkData> &chunks,
    const map<size_t, size_t> &chunk_to_key_mapping)
{
    map<size_t, uint64_t> index_to_key;
    for (const auto &chunk : chunks)
    {
        index_to_key[chunk.header.index] = chunk.header.key;
    }

    printf("Decrypting chunks...\n");
    vector<uint8_t *> decrypted_chunks(chunks.size());

    for (const auto &chunk : chunks)
    {
        size_t chunk_id = chunk.header.index;

        if (chunk_to_key_mapping.find(chunk_id) == chunk_to_key_mapping.end())
        {
            fprintf(stderr, "Error: No mapping found for chunk_id=%zu\n", chunk_id);
            continue;
        }

        size_t key_chunk_id = chunk_to_key_mapping.at(chunk_id);

        if (index_to_key.find(key_chunk_id) == index_to_key.end())
        {
            fprintf(stderr, "Error: Key chunk %zu not found for chunk %zu\n", key_chunk_id, chunk_id);
            continue;
        }

        uint64_t decryption_key = index_to_key[key_chunk_id];

        printf("Chunk %zu: using key from chunk %zu (key=%llu)\n",
               chunk_id, key_chunk_id, decryption_key);

        uint8_t *decrypted_data = (uint8_t *)malloc(chunk.header.chunk_size);
        memcpy(decrypted_data, chunk.encrypted_data, chunk.header.chunk_size);
        xor_encdec_8(decrypted_data, chunk.header.chunk_size, decryption_key);

        uint32_t computed_crc = crc32(decrypted_data, chunk.header.chunk_size);

        if (computed_crc == chunk.header.crc32)
        {
            printf("Chunk %zu decrypted successfully (CRC32 verified)\n", chunk_id);
            decrypted_chunks[chunk_id] = decrypted_data;
        }
        else
        {
            fprintf(stderr, "Chunk %zu CRC32 mismatch! Expected=%llu, Got=%u\n",
                    chunk_id, chunk.header.crc32, computed_crc);
            free(decrypted_data);
            decrypted_chunks[chunk_id] = nullptr;
        }
    }

    return decrypted_chunks;
}

vector<uint8_t> assemble_final_data(
    const vector<uint8_t *> &decrypted_chunks,
    const vector<ChunkData> &chunks)
{
    printf("\nAssembling final data.\n");
    vector<uint8_t> final_data;

    for (size_t i = 0; i < decrypted_chunks.size(); i++)
    {
        if (decrypted_chunks[i] != nullptr)
        {
            for (const auto &chunk : chunks)
            {
                if (chunk.header.index == i)
                {
                    final_data.insert(final_data.end(),
                                      decrypted_chunks[i],
                                      decrypted_chunks[i] + chunk.header.chunk_size);
                    break;
                }
            }
        }
        else
        {
            fprintf(stderr, "Warning: Chunk %zu is missing or invalid\n", i);
        }
    }

    return final_data;
}

void save_final_data(const vector<uint8_t> &final_data)
{
    uint32_t final_crc = crc32(final_data.data(), final_data.size());
    printf("\nFinal data size: %zu bytes\n", final_data.size());
    printf("Final CRC32: %u\n", final_crc);

    ofstream output_file("../decoded_chunks.txt", ios::binary);
    if (!output_file)
    {
        fprintf(stderr, "Error: Cannot create output file\n");
    }
    else
    {
        output_file.write((const char *)final_data.data(), final_data.size());
        output_file.close();
        printf("Successfully saved to decoded_chunks.txt\n");
    }
}

void cleanup_chunks(vector<ChunkData> &chunks, vector<uint8_t *> &decrypted_chunks)
{
    for (auto &chunk : chunks)
    {
        if (chunk.encrypted_data)
        {
            free(chunk.encrypted_data);
        }
    }

    for (auto *decrypted : decrypted_chunks)
    {
        if (decrypted)
        {
            free(decrypted);
        }
    }
}

void get_hint2(uint8_t *memory, size_t memory_size)
{
    map<size_t, size_t> chunk_to_key_mapping = parse_hint_and_create_mapping();

    if (chunk_to_key_mapping.empty())
    {
        fprintf(stderr, "Failed to create chunk mapping\n");
        return;
    }

    vector<ChunkData> chunks = extract_corrupted_chunks(memory);
    if (chunks.empty())
    {
        fprintf(stderr, "No chunks found\n");
        return;
    }

    vector<uint8_t *> decrypted_chunks = decrypt_and_verify_chunks(chunks, chunk_to_key_mapping);

    vector<uint8_t> final_data = assemble_final_data(decrypted_chunks, chunks);

    save_final_data(final_data);

    cleanup_chunks(chunks, decrypted_chunks);

    google::protobuf::ShutdownProtobufLibrary();
}

int main()
{
    const char *fname = "../mysterious_heap";
    uint8_t *memory = NULL;
    size_t memory_size = mysterious_heap_load(&memory, fname);
    get_hint1(memory, memory_size);
    get_hint2(memory, memory_size);
    free(memory);
    return 0;
}