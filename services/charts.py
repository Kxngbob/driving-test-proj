from matplotlib.figure import Figure

def create_pass_chart(rows):
    provinces = {}
    for r in rows:
        prov = r["desc_provincia"]
        provinces.setdefault(prov, 0)
        provinces[prov] += r["num_aptos"]

    fig = Figure(figsize=(6, 4))
    ax = fig.add_subplot(111)

    ax.bar(provinces.keys(), provinces.values())
    ax.set_title("Passed Exams by Province")
    ax.tick_params(axis='x', rotation=45)

    return fig
