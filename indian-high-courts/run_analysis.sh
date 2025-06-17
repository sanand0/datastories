#!/bin/bash

# Indian High Courts Judgment Dataset Analysis
# Complete analysis script for all 5 research questions

echo "Starting Indian High Courts Dataset Analysis..."
echo "=============================================="

# Create results directory
mkdir -p results

# Check if DuckDB is available
if ! command -v duckdb &> /dev/null; then
    echo "Error: DuckDB is not installed. Please install DuckDB first."
    echo "Visit: https://duckdb.org/docs/installation/"
    exit 1
fi

echo "✓ DuckDB found"

# Function to run query with error handling
run_query() {
    local query_file=$1
    local output_file=$2
    local description=$3
    
    echo ""
    echo "Running: $description"
    echo "Query: $query_file"
    echo "Output: $output_file"
    
    if duckdb -csv < "$query_file" > "results/$output_file" 2>&1; then
        echo "✓ Success: Analysis completed"
        lines=$(wc -l < "results/$output_file")
        echo "  Generated $lines lines of results"
    else
        echo "✗ Failed: Check results/$output_file for error details"
        return 1
    fi
}

# Run all analyses
echo ""
echo "Executing Research Questions..."
echo "=============================="

# Query 1: Court Efficiency Analysis
run_query "query_1_court_efficiency.sql" "court_efficiency_results.csv" "Court Efficiency and Backlog Analysis"

# Query 2: Seasonal Justice Analysis
run_query "query_2_seasonal_justice.sql" "seasonal_justice_results.csv" "Seasonal Justice Pattern Analysis"

# Query 3: Geographic Disparities Analysis
run_query "query_3_geographic_disparities.sql" "geographic_disparities_results.csv" "Geographic Disparities Analysis"

# Query 4: Constitutional Cases Analysis
run_query "query_4_constitutional_cases.sql" "constitutional_cases_results.csv" "Constitutional Cases Trend Analysis"

# Query 5: Bench Strength Analysis
run_query "query_5_bench_strength_impact.sql" "bench_strength_results.csv" "Bench Strength Impact Analysis"

# Query 6: UAPA Bail Patterns Analysis
run_query "query_6_uapa_bail_patterns.sql" "uapa_bail_patterns_results.csv" "UAPA Bail Denial Patterns Analysis"

# Sample UAPA Cases Extract
run_query "query_sample_uapa_cases.sql" "sample_uapa_cases_results.csv" "Sample UAPA Cases with Details"

# Summary
echo ""
echo "Analysis Complete!"
echo "=================="
echo "Results saved in the 'results/' directory:"
ls -la results/

echo ""
echo "Next Steps:"
echo "- Review the CSV files for insights"
echo "- Use the data for visualization and reporting"
echo "- Refer to README.md for interpretation guidance"
echo ""
echo "For questions or issues, refer to the methodology section in README.md"