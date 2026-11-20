"""
External merge sort on a pretend disk
Topic: 02.13  |  Priority: P2

Problem
-------
Sections 6 and 7 of the chapter. Sort a file that is much bigger than
memory. You may hold at most `memory` records at once, and you may have at
most `fan_in` files open for reading at once. Everything else lives on the
disk, and every record you read or write is counted.

    name = external_sort(disk, "input", memory=100, fan_in=10)
    # 10,000 records -> 100 sorted runs of 100 -> merge 10 at a time
    # -> 10 runs of 1,000 -> 1 run of 10,000. Two merge passes.

external_sort(disk, name, memory, fan_in) -> str
  - Sort the records of file `name` by their .key. Return the name of a file
    on the disk that holds every record once, in sorted order.
  - Stable: records with equal keys come out in the order they went in
    (record.value tells the tests where each record started).
  - Records are not comparable to each other; their .key objects are.
    Tie-break heap entries with something that is never equal, for example
    (record.key, run_number, record).
  - If the whole file fits in one run, that run is the answer: don't copy it.

The disk (the tests build it; see the Disk class in test_external_sort.py)
  disk.reader(name)  an iterator over the file's records, front to back.
                     It counts as open until you reach the end or call
                     .close() on it.
  disk.writer()      a new empty file. w.write(record) appends a record you
                     got from a reader; w.name is the file's name.
  Use only reader(), writer(), write(), close(), .name, and each record's
  .key and .value. A test checks the source: reaching into the disk's
  bookkeeping (disk.files, or a key's raw value key._v) is not allowed.
  Rules the disk enforces, raising an error the moment you break one:
  - At most memory + 1 records alive in your program at once (the extra one
    is the record in your hand while you flush a full buffer). Keys you
    copied out don't count, but you can only write records, not keys.
    A full buffer counts until you drop it: buf = list(islice(reader,
    memory)) in a loop builds the new list while the old one is still
    alive, so clear or delete the old buffer before you fill the next.
  - At most fan_in readers open at once.
  - At most n * (1 + P) record reads and n * (1 + P) record writes in total,
    where n is the number of records, R = ceil(n / memory) is the number of
    full-memory runs, and P = ceil(log_fan_in(R)) is the number of merge
    passes (0 when R <= 1).

Target: about n log(memory) comparisons to make the runs, plus about
log(fan_in) per record per merge pass. O(memory) records in RAM.

What the tests measure
----------------------
- Reads and writes against the budget above. Runs smaller than `memory`
  make more runs, which can need an extra pass. Two-way merging needs
  log2(R) passes instead of log_fan_in(R): with R = 100 and fan_in = 10
  that's 7 passes instead of 2, so it runs out of reads mid-sort.
- Key comparisons: with fan_in = 256, finding the smallest of 256 fronts by
  looking at all of them costs 255 comparisons per record. A heap costs
  about 2 * log2(256) = 16. The budget is 120 key comparisons per record
  for the whole sort (runs plus merge).
- Output: sorted, stable, every record exactly once.

Before you code (say it out loud)
---------------------------------
1. Why make each run as big as memory allows? What does halving the run
   size do to R, and to P?
2. Why can't you open all R runs at once on a real disk? What does each
   open run need in memory?
3. How many times is each record read and written, in total? Say it for
   R = 100 and fan_in = 10.
4. Why does the tie-break in the heap make the sort stable?

Run:  pytest -k external_sort
"""


def external_sort(disk, name, memory, fan_in):
    raise NotImplementedError
