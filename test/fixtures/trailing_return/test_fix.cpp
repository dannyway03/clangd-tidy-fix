// Return type on a separate line from the function name.
// This exposes diagnostic position vs first-replacement position discrepancy:
// clangd reports the diagnostic at 'foo' (line 4), but the first replacement
// targets 'int' (line 3). FileOffset must match the stream output line.
int
foo(int x) {
    return x;
}
