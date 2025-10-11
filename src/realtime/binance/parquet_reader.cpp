#include <iostream>
#include <memory>

// Arrow includes
#include <arrow/api.h>
#include <arrow/io/api.h>
#include <parquet/arrow/reader.h>
#include <parquet/exception.h>

// Function to read a Parquet file and print some info
void read_parquet_file(const std::string& file_path) {
    // 1. Open the Parquet file
    std::shared_ptr<arrow::io::ReadableFile> infile;
    PARQUET_ASSIGN_OR_THROW(
        infile,
        arrow::io::ReadableFile::Open(file_path, arrow::default_memory_pool())
    );

    // 2. Create a Parquet file reader
    std::unique_ptr<parquet::arrow::FileReader> reader;
    PARQUET_ASSIGN_OR_THROW(
        reader,
        parquet::arrow::OpenFile(infile, arrow::default_memory_pool())
    );

    // 3. Read the file into an Arrow Table
    std::shared_ptr<arrow::Table> table;
    PARQUET_THROW_NOT_OK(reader->ReadTable(&table));

    // 4. Access the data
    std::cout << "========================================" << std::endl;
    std::cout << "Successfully read Parquet file: " << file_path << std::endl;
    std::cout << "Number of rows read: " << table->num_rows() << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Number of columns: " << table->num_columns() << std::endl;

    // Print column names
    std::cout << "Columns:" << std::endl;
    for (const auto& field : table->schema()->fields()) {
        std::cout << "  - " << field->name() << " (" << field->type()->ToString() << ")" << std::endl;
    }

    // Example: Access data from the first column (if it's a numeric type)
    // This is just a conceptual example. You'd need to know the column type.
    if (table->num_rows() > 0 && table->num_columns() > 0) {
        auto first_column = table->column(0);
        // You would need to cast to the specific array type, e.g., DoubleArray, Int64Array
        // For example, if the first column is of type double:
        // auto double_array = std::static_pointer_cast<arrow::DoubleArray>(first_column->chunk(0));
        // if (double_array) {
        //     std::cout << "First value in the first column: " << double_array->Value(0) << std::endl;
        // }
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <path_to_parquet_file>" << std::endl;
        return 1;
    }

    try {
        read_parquet_file(argv[1]);
    } catch (const parquet::ParquetException& e) {
        std::cerr << "Parquet error: " << e.what() << std::endl;
        return 1;
    } catch (const std::exception& e) {
        std::cerr << "An error occurred: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
