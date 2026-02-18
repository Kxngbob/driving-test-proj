from matplotlib.figure import Figure


def create_pass_chart(grouped_rows):
    """
    grouped_rows must come from:
    db.get_grouped_results(...)
    """

    provinces = []
    aptos = []
    no_aptos = []

    for row in grouped_rows:
        provinces.append(row["desc_provincia"])
        aptos.append(row["total_aptos"])
        no_aptos.append(row["total_no_aptos"])

    fig = Figure(figsize=(7, 4))
    ax = fig.add_subplot(111)

    # Stacked bar chart
    ax.bar(provinces, aptos, label="Aptos")
    ax.bar(provinces, no_aptos, bottom=aptos, label="No Aptos")

    ax.set_title("Exam Results (Aptos vs No Aptos)")
    ax.set_ylabel("Number of Students")
    ax.legend()

    ax.tick_params(axis='x', rotation=45)

    fig.tight_layout()

    return fig
