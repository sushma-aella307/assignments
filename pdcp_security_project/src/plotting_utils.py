# pdcp_security_project/src/plotting_utils.py
import matplotlib
matplotlib.use('Agg') # Use non-interactive backend for server-side plotting
import matplotlib.pyplot as plt
import os
import time

def generate_summary_plot(stats, output_dir="static/plots"):
    """
    Generates a bar chart summarizing packet statistics.
    Saves the plot to a file and returns the file path.
    """
    if not stats:
        return None

    labels = []
    values = []

    if 'successful_deliveries' in stats:
        labels.append('Delivered')
        values.append(stats['successful_deliveries'])
    if 'discarded_integrity_failures' in stats:
        labels.append('Integrity Fail')
        values.append(stats['discarded_integrity_failures'])
    if 'discarded_duplicates' in stats:
        labels.append('Duplicates')
        values.append(stats['discarded_duplicates'])
    if 'discarded_channel_corruption' in stats: # Assuming this key might exist from PDCPReceiver
        labels.append('Corrupted (Chan)')
        values.append(stats['discarded_channel_corruption'])
    # Add other stats as needed

    if not labels: # No data to plot
        return None

    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values, color=['green', 'red', 'orange', 'brown', 'grey'])
    plt.ylabel('Number of Packets')
    plt.title('PDCP Packet Delivery Summary')
    plt.xticks(rotation=15, ha="right") # Rotate labels if they overlap
    plt.tight_layout() # Adjust layout to prevent labels from being cut off

    # Add counts on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 0.05 * max(values, default=1), # Adjust offset
                 int(yval), va='bottom', ha='center')


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Unique filename to avoid browser caching issues if plots are regenerated
    plot_filename = f"summary_plot_{int(time.time())}.png"
    plot_filepath = os.path.join(output_dir, plot_filename)
    
    try:
        plt.savefig(plot_filepath)
        plt.close() # Close the figure to free memory
        # Return the path relative to the 'static' folder for URL generation
        return os.path.join("plots", plot_filename) 
    except Exception as e:
        print(f"Error saving plot: {e}")
        plt.close()
        return None

if __name__ == '__main__':
    # Example Usage:
    mock_stats = {
        'successful_deliveries': 85,
        'discarded_integrity_failures': 10,
        'discarded_duplicates': 3,
        'discarded_channel_corruption': 2
    }
    # Create static/plots directory if it doesn't exist for the test
    if not os.path.exists("static/plots"):
        os.makedirs("static/plots")

    plot_url = generate_summary_plot(mock_stats)
    if plot_url:
        print(f"Plot generated and saved. Access it via: static/{plot_url}")
    else:
        print("Failed to generate plot.")