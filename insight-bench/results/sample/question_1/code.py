import pandas as pd
from insightbench.tools import save_json, fix_fnames, plot_countplot

# Load the dataset
data_path = '/home/yzhang6375/NL2INS/insight-bench/data/notebooks/csvs/flag-1.csv'
df = pd.read_csv(data_path)

# Filter for resolved tickets
resolved_tickets = df[df['state'] == 'Resolved']

# Group by assigned personnel and category, then count the number of tickets
assigned_counts = resolved_tickets.groupby(['assigned_to', 'category']).size().reset_index(name='count')

# Find the assigned personnel with the highest number of resolved tickets
highest_assigned = assigned_counts.loc[assigned_counts['count'].idxmax()]

# Extract the personnel name and category
highest_personnel = highest_assigned['assigned_to']  # Assigned personnel with the highest count
highest_category = highest_assigned['category']      # Category they primarily handle

# Prepare data for the plot
plot_data = assigned_counts.groupby('assigned_to')['count'].sum().reset_index()
plot_data = plot_data.sort_values(by='count', ascending=False).head(10)  # Top 10 personnel

# Plot the count of resolved tickets by assigned personnel
plot_title = 'Top 10 Assigned Personnel by Resolved Tickets'
plot_countplot(df=plot_data, plot_column='assigned_to', plot_title=plot_title)

# Prepare stats for JSON
stats_data = {
    'name': "Resolved Tickets by Assigned Personnel",
    'description': "Counts of resolved tickets for each assigned personnel.",
    'value': plot_data.to_dict(orient='records')
}

# Save stats JSON
save_json(stats_data, ftype='stat')

# Prepare x_axis JSON
x_axis_data = {
    'name': "Assigned Personnel",
    'description': "Top assigned personnel handling resolved tickets.",
    'value': plot_data['assigned_to'].tolist()
}
save_json(x_axis_data, ftype='x_axis')

# Prepare y_axis JSON
y_axis_data = {
    'name': "Count of Resolved Tickets",
    'description': "Number of resolved tickets handled by each personnel.",
    'value': plot_data['count'].tolist()
}
save_json(y_axis_data, ftype='y_axis')

# Fix filenames for plots and stats
fix_fnames()