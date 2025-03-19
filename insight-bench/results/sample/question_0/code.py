import pandas as pd
from insightbench.tools import generate_wordcloud, plot_countplot, save_json, fix_fnames

# Load the dataset from the given path
data_path = '/home/yzhang6375/NL2INS/insight-bench/data/notebooks/csvs/flag-1.csv'  # Path to the CSV file
df = pd.read_csv(data_path)  # Read the CSV file into a DataFrame

# Create a count plot of ticket resolutions by category
plot_column = 'category'  # The column we want to plot
plot_title = 'Ticket Resolutions by Category'  # Title of the plot
plot_countplot(df, plot_column, plot_title)  # Generate the count plot and save it

# Prepare data for stats json
stats_data = {
    'name': 'Ticket Resolutions by Category',
    'description': 'A count of ticket resolutions categorized by type.',
    'value': df[plot_column].value_counts().to_dict()
}
save_json(stats_data, 'stat')  # Save stats data as JSON

# Prepare data for x_axis json (category names)
x_axis_data = {
    'name': 'Ticket Categories',
    'description': 'Different categories for ticket resolutions.',
    'value': df[plot_column].unique()[:50].tolist()  # Limit to top 50 categories
}
save_json(x_axis_data, 'x_axis')  # Save x axis data as JSON

# Prepare data for y_axis json (counts of resolutions)
y_axis_data = {
    'name': 'Counts of Resolutions',
    'description': 'Counts of resolutions for the respective categories.',
    'value': df[plot_column].value_counts().head(50).tolist()  # Limit to top 50 counts
}
save_json(y_axis_data, 'y_axis')  # Save y axis data as JSON

# Fix the filenames of saved plots and stats
fix_fnames()  # Rename all plot and stat files in the current directory