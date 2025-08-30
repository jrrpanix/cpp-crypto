#include <arrow/api.h>
#include <arrow/io/api.h>
#include <parquet/arrow/reader.h>
#include <iostream>
#include <memory>

int main(int argc, char** argv) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <file.parquet>" << std::endl;
        return 1;
    }

    std::string filename = argv[1];
    std::shared_ptr<arrow::io::ReadableFile> infile;
    PARQUET_ASSIGN_OR_THROW(
        infile,
        arrow::io::ReadableFile::Open(filename)
    );

    std::unique_ptr<parquet::arrow::FileReader> reader;
    PARQUET_THROW_NOT_OK(
        parquet::arrow::OpenFile(infile, arrow::default_memory_pool(), &reader)
    );

    std::shared_ptr<arrow::Table> table;
    PARQUET_THROW_NOT_OK(reader->ReadTable(&table));

    // Print schema
    std::cout << "Schema: " << table->schema()->ToString() << std::endl;

    // Print first 5 rows
    std::shared_ptr<arrow::RecordBatch> batch;
    arrow::TableBatchReader batch_reader(*table);
    int row_count = 0;
    while (batch_reader.ReadNext(&batch).ok() && batch) {
        for (int i = 0; i < batch->num_rows() && row_count < 5; ++i, ++row_count) {
            for (int j = 0; j < batch->num_columns(); ++j) {
                std::cout << batch->column(j)->ToString() << " ";
            }
            std::cout << std::endl;
        }
        if (row_count >= 5) break;
    }

    return 0;
}
