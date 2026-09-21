# clangd-tidy Parity Report — 2026-09-21

Compares `clangd-tidy --export-fixes` YAML format against `clang-tidy-20 --export-fixes`
for each check enabled in sv_mot's `.clang-tidy` that has auto-fixes.

## Legend
| Status | Meaning |
|--------|---------|
| ✅ PASS | YAML format matches: FileOffset line consistent, Replacements present |
| ❌ FAIL | Mismatch detected — needs fix in replacements.py or main_cli.py |
| ⚠️ NO_FIX_CLANGD | clangd produces no code actions for this check |
| 🚫 NO_TRIGGER | Fixture code doesn't trigger the check — improve fixture |
| 💥 ERROR | Tool crash or unexpected error |
| ⏭️ SKIP | Covered by existing pytest fixture |

## Summary
- ✅ PASS: 50
- ⚠️ NO_FIX_CLANGD: 1
- ⏭️ SKIP: 3

## Results

| Check | Status | CT diags | Clangd diags | Issues |
|-------|--------|----------|--------------|--------|
| `readability-container-size-empty` | ⚠️ NO_FIX_CLANGD | 1 | 0 | - |
| `cppcoreguidelines-init-variables` | ✅ PASS | 1 | 1 | - |
| `cppcoreguidelines-pro-type-cstyle-cast` | ✅ PASS | 1 | 1 | - |
| `misc-static-assert` | ✅ PASS | 1 | 1 | - |
| `misc-unused-alias-decls` | ✅ PASS | 1 | 1 | - |
| `misc-unused-using-decls` | ✅ PASS | 1 | 1 | - |
| `modernize-avoid-bind` | ✅ PASS | 1 | 1 | - |
| `modernize-concat-nested-namespaces` | ✅ PASS | 1 | 1 | - |
| `modernize-deprecated-headers` | ✅ PASS | 1 | 1 | - |
| `modernize-loop-convert` | ✅ PASS | 1 | 1 | - |
| `modernize-make-shared` | ✅ PASS | 1 | 1 | - |
| `modernize-make-unique` | ✅ PASS | 1 | 1 | - |
| `modernize-pass-by-value` | ✅ PASS | 1 | 1 | - |
| `modernize-redundant-void-arg` | ✅ PASS | 2 | 2 | - |
| `modernize-replace-random-shuffle` | ✅ PASS | 1 | 1 | - |
| `modernize-return-braced-init-list` | ✅ PASS | 1 | 1 | - |
| `modernize-shrink-to-fit` | ✅ PASS | 1 | 1 | - |
| `modernize-type-traits` | ✅ PASS | 1 | 1 | - |
| `modernize-unary-static-assert` | ✅ PASS | 1 | 1 | - |
| `modernize-use-auto` | ✅ PASS | 1 | 1 | - |
| `modernize-use-bool-literals` | ✅ PASS | 1 | 1 | - |
| `modernize-use-default-member-init` | ✅ PASS | 1 | 1 | - |
| `modernize-use-emplace` | ✅ PASS | 1 | 1 | - |
| `modernize-use-equals-default` | ✅ PASS | 2 | 2 | - |
| `modernize-use-equals-delete` | ✅ PASS | 2 | 2 | - |
| `modernize-use-nodiscard` | ✅ PASS | 2 | 2 | - |
| `modernize-use-noexcept` | ✅ PASS | 1 | 1 | - |
| `modernize-use-override` | ✅ PASS | 1 | 1 | - |
| `modernize-use-starts-ends-with` | ✅ PASS | 1 | 1 | - |
| `modernize-use-std-numbers` | ✅ PASS | 1 | 1 | - |
| `modernize-use-transparent-functors` | ✅ PASS | 1 | 1 | - |
| `modernize-use-uncaught-exceptions` | ✅ PASS | 1 | 1 | - |
| `modernize-use-using` | ✅ PASS | 1 | 1 | - |
| `performance-avoid-endl` | ✅ PASS | 1 | 1 | - |
| `performance-for-range-copy` | ✅ PASS | 1 | 1 | - |
| `performance-inefficient-vector-operation` | ✅ PASS | 1 | 1 | - |
| `performance-move-const-arg` | ✅ PASS | 1 | 1 | - |
| `performance-unnecessary-copy-initialization` | ✅ PASS | 1 | 1 | - |
| `performance-unnecessary-value-param` | ✅ PASS | 1 | 1 | - |
| `readability-const-return-type` | ✅ PASS | 1 | 1 | - |
| `readability-delete-null-pointer` | ✅ PASS | 1 | 1 | - |
| `readability-qualified-auto` | ✅ PASS | 1 | 1 | - |
| `readability-redundant-control-flow` | ✅ PASS | 1 | 1 | - |
| `readability-redundant-member-init` | ✅ PASS | 1 | 1 | - |
| `readability-redundant-smartptr-get` | ✅ PASS | 1 | 1 | - |
| `readability-redundant-string-cstr` | ✅ PASS | 1 | 1 | - |
| `readability-redundant-string-init` | ✅ PASS | 1 | 1 | - |
| `readability-simplify-boolean-expr` | ✅ PASS | 2 | 2 | - |
| `readability-string-compare` | ✅ PASS | 1 | 1 | - |
| `readability-uniqueptr-delete-release` | ✅ PASS | 1 | 1 | - |
| `readability-use-std-min-max` | ✅ PASS | 2 | 2 | - |
| `misc-include-cleaner` | ⏭️ SKIP | 0 | 0 | - |
| `modernize-use-nullptr` | ⏭️ SKIP | 0 | 0 | - |
| `modernize-use-trailing-return-type` | ⏭️ SKIP | 0 | 0 | - |

## Details

### ⚠️ `readability-container-size-empty`
**Status:** NO_FIX_CLANGD | CT: 1 diag(s) | Clangd: 0 diag(s)

**Notes:**
- clangd produced neither stream diagnostics nor YAML fixes

### ✅ `cppcoreguidelines-init-variables`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `cppcoreguidelines-pro-type-cstyle-cast`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `misc-static-assert`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `misc-unused-alias-decls`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `misc-unused-using-decls`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-avoid-bind`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-concat-nested-namespaces`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-deprecated-headers`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-loop-convert`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-make-shared`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-make-unique`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-pass-by-value`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-redundant-void-arg`
**Status:** PASS | CT: 2 diag(s) | Clangd: 2 diag(s)

### ✅ `modernize-replace-random-shuffle`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-return-braced-init-list`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-shrink-to-fit`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-type-traits`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-unary-static-assert`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-auto`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-bool-literals`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-default-member-init`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-emplace`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-equals-default`
**Status:** PASS | CT: 2 diag(s) | Clangd: 2 diag(s)

### ✅ `modernize-use-equals-delete`
**Status:** PASS | CT: 2 diag(s) | Clangd: 2 diag(s)

### ✅ `modernize-use-nodiscard`
**Status:** PASS | CT: 2 diag(s) | Clangd: 2 diag(s)

### ✅ `modernize-use-noexcept`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-override`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-starts-ends-with`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-std-numbers`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-transparent-functors`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-uncaught-exceptions`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `modernize-use-using`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `performance-avoid-endl`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `performance-for-range-copy`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `performance-inefficient-vector-operation`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `performance-move-const-arg`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `performance-unnecessary-copy-initialization`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `performance-unnecessary-value-param`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-const-return-type`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-delete-null-pointer`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-qualified-auto`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-redundant-control-flow`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-redundant-member-init`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-redundant-smartptr-get`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-redundant-string-cstr`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-redundant-string-init`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-simplify-boolean-expr`
**Status:** PASS | CT: 2 diag(s) | Clangd: 2 diag(s)

### ✅ `readability-string-compare`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-uniqueptr-delete-release`
**Status:** PASS | CT: 1 diag(s) | Clangd: 1 diag(s)

### ✅ `readability-use-std-min-max`
**Status:** PASS | CT: 2 diag(s) | Clangd: 2 diag(s)

### ⏭️ `misc-include-cleaner`
**Status:** SKIP | CT: 0 diag(s) | Clangd: 0 diag(s)

**Notes:**
- Covered by existing pytest fixture

### ⏭️ `modernize-use-nullptr`
**Status:** SKIP | CT: 0 diag(s) | Clangd: 0 diag(s)

**Notes:**
- Covered by existing pytest fixture

### ⏭️ `modernize-use-trailing-return-type`
**Status:** SKIP | CT: 0 diag(s) | Clangd: 0 diag(s)

**Notes:**
- Covered by existing pytest fixture
