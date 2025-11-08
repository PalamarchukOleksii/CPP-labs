# Task 1

In this task, I give you a mysterious binary file. You have to figure out a way to extract
an important data from it and save it to the disk.

On your journey you will encounter hints on
how to proceed, but first, let me give you the
first fundamental information regarding the file.

The general structure of this file is a heap, a pool with intrusive list to be precise. The file starts with a header:

```
Pool_Node (header):
Pool_Node *prev;  // pointer to a previous node, may be NULL at the first node.
Pool_Node *next;  // pointer to a next node, may be NULL at the last node.
size_t data_size;  // size of the node's payload
int64_t flags;  // some bit flags describing the info about the node
-----
bytes of data [data_size]
```

The struct representing this header is already implemented in `mysterious_heap.cpp` - a file, which you have to finish.

The first hint is as follows:

```
Look for the nodes with POOL_FLAG_IS_INTERESTING bit set in the flag.

each interesting node's payload starts with a header

struct Interesting_Pool_Node {
    int64_t hint_key;
    int64_t hint_length;
};

after which goes the hint and the rest of the payload in the node.
```

How do you read this hint? Well, its bytes start right after the Interesting_Pool_Node header and take hint_length bytes. However, it's encrypted with a key hint_key. Use xor_encdec8 function to decrypt it.

We also use crc32 hashes in this work, mostly for debugging. The example of usage is already in the main function. By the way, make sure the printed hash of the mysterious_heap file is 2159869300.