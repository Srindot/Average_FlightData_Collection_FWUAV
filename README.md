# Flapping Wing UAV Data Collection

This repository is designed for collecting average data for a flapping wing UAV. The script `acg_coeff_data_collection.py` runs the necessary data collection, and the resulting data is saved into a CSV file called `AverageFlightData.csv`.

## Getting Started

Follow the steps below to set up and run the data collection script on your local machine.

### Prerequisites

Make sure you have Python installed on your system. You can check by running:

```bash
python --version
```

If Python is not installed, download and install the latest version from [here](https://www.python.org/downloads/).

### Installation

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/Srindot/Average_Flight_Data_Collection.git
   ```

2. Navigate to the project directory:

   ```bash
   cd Average_Flight_Data_Collection
   ```

3. (Optional) Create and activate a virtual environment to manage dependencies:

   - On Windows:

     ```bash
     python -m venv venv
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

4. Install the required dependencies by running the following:

   ```bash
   pip install pterasoftware
   ```

### Running the Data Collection Script

1. Once the environment is set up, ensure you're in the project directory.

2. Run the data collection script:

   ```bash
   python acg_coeff_data_collection.py
   ```

3. The script will collect the data and save it into a CSV file called `AverageFlightData.csv`. You should see this file in the same directory.

### Output

- `AverageFlightData.csv`: This file contains the average data collected during the flight tests.

### Troubleshooting

- If you encounter issues with missing dependencies, try running:

   ```bash
   pip install -r requirements.txt
   ```

# FWUAV-Average-Flight-Data-Collection
