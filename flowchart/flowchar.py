# Vertical tree diagram for PCB career paths (full code)
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# Build directed graph
G = nx.DiGraph()
root = "PCB Stream"
G.add_node(root)

# Categories and simplified options
categories = {
    "Medical & Healthcare": ["MBBS / BDS", "BAMS / BHMS", "Nursing / Paramedical"],
    "Allied Science & Research": ["B.Sc. Biology", "Biotechnology", "Forensic Science"],
    "Agriculture & Environment": ["B.Sc. Agriculture", "Forestry", "Environmental Science"],
    "Professional Courses": ["Pharmacy", "Veterinary", "Biomedical Engg."],
    "Other Careers": ["NEET (Entrance)", "UPSC / Govt. Exams", "Teaching"]
}

# Add edges
for cat, subs in categories.items():
    G.add_node(cat)
    G.add_edge(root, cat)
    for sub in subs:
        G.add_node(sub)
        G.add_edge(cat, sub)

# Create a vertical tree layout manually
pos = {}
# root at top center
pos[root] = (0.0, 0.0)

# place categories in the second row equally spaced
n_cat = len(categories)
cat_xs = np.linspace(-2.5, 2.5, n_cat)
cat_y = -1.0
for x, cat in zip(cat_xs, categories.keys()):
    pos[cat] = (x, cat_y)

# place subnodes in third row grouped under their category
sub_y = -2.2
for x, (cat, subs) in zip(cat_xs, categories.items()):
    n_sub = len(subs)
    if n_sub == 1:
        sub_xs = [x]
    else:
        # span controls horizontal spread of children under each category
        span = 0.6
        sub_xs = np.linspace(x - span, x + span, n_sub)
    for sx, sub in zip(sub_xs, subs):
        pos[sub] = (sx, sub_y)

# Draw the graph (vertical tree)
plt.figure(figsize=(8, 10))
nx.draw_networkx_nodes(G, pos, node_size=2500)
nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold")
nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrows=False, width=1.2)

plt.title("Vertical Tree: Career Paths After Choosing PCB Stream", fontsize=14, fontweight="bold")
plt.axis("off")
plt.tight_layout()
plt.show()
