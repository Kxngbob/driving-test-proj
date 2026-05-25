from matplotlib.figure import Figure


def create_pass_chart(grouped_rows, group_label="Group"):
    """
    Creates a stacked bar chart from grouped SQL data.

    Expected columns from database.get_grouped_results():
    - group_name
    - total_aptos
    - total_no_aptos
    - total_presentados
    """

    labels = []
    passed = []
    failed = []

    for row in grouped_rows:
        labels.append(str(row["group_name"]))
        passed.append(row["total_aptos"] or 0)
        failed.append(row["total_no_aptos"] or 0)

    fig = Figure(figsize=(8, 4.5))
    ax = fig.add_subplot(111)

    if not labels:
        ax.set_title("No data available for selected filters")
        ax.set_ylabel("Number of students")
        fig.tight_layout()
        return fig

    ax.bar(labels, passed, label="Passed")
    ax.bar(labels, failed, bottom=passed, label="Failed")

    ax.set_title(f"Exam Results by {group_label}")
    ax.set_ylabel("Number of students")
    ax.legend()

    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()

    return fig