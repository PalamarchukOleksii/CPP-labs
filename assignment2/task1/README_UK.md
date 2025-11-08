# Task 1

В даному завданні, я даю вам загадковий бінарний файл (mysterious heap). Вам потрібно придумати і витягнути важливі дані з нього, а потім зберегти на диск.

На вашому шляху ви знайдете підказки щодо наступних кроків. Та спочатку, надам вам трохи основної інформації щодо файлу.

Загальна структура цього файлу - куча (heap) - pool з вбудованим двозвʼязним списком. Файл починається із заголовку:

```
Pool_Node (header):
Pool_Node *prev;  // pointer to a previous node, may be NULL at the first node.
Pool_Node *next;  // pointer to a next node, may be NULL at the last node.
size_t data_size;  // size of the node's payload
int64_t flags;  // some bit flags describing the info about the node
-----
bytes of data [data_size]
```

Структура, що представляє цей заголовок вже реалізована в `mysterious_heap.cpp` - файлі, який вам потрібно завершити.

Ваша перша підказка звучить так:

```
Look for the nodes with POOL_FLAG_IS_INTERESTING bit set in the flag.

each interesting node's payload starts with a header

struct Interesting_Pool_Node {
    int64_t hint_key;
    int64_t hint_length;
};

after which goes the hint and the rest of the payload in the node.
```

Як же прочитати наступну підказку? Ну, її байти починаються одразу після іще одного заголовку Interesting_Pool_Node та займають hint_length байтів памʼяті. Однак, байти зашифровані ключем hint_key. Скористайтесь функцією xor_encdec8 щоб її розшифрувати.

Ми також використовуватимемо CRC32 геші в цій роботі, в основному для дебаггінгу. Приклад використання такого гешу вже реалізований в функції main. До речі, переконайтесь, що геш вхідного файлу mysterious_heap, що виводиться в stdout дорівнює 2159869300.