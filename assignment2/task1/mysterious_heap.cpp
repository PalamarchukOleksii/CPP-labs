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

#include "crc32.h"

#define POOL_FLAG_IS_FREE 0x0001
#define POOL_FLAG_IS_INTERESTING 0x0004
// ??

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
        }
        p = p->next;
    }
}

int main()
{
    // Set path to heap file here!!
    const char *fname = "../mysterious_heap";
    uint8_t *memory = NULL;
    size_t memory_size = mysterious_heap_load(&memory, fname);
    get_hint1(memory, memory_size);

    return 0;
}