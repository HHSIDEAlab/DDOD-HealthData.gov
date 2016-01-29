import jinja2
import os
import data_json_counts  # Code to run data.json dataset counts

RENDERED_PATH = os.path.abspath('generated/')+'/'
TEMPLATE_PATH = os.path.abspath('templates/')+'/'
TEMPLATE_NAME = 'dataset_count_by_source.html'

def save_data():
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH))
    template = env.get_template(TEMPLATE_NAME)
    csv_data = data_json_counts.update_csv_from_snapshots()
    rendered_html = template.render(csv_data=csv_data)

    print( "Saving HTML file (size: "+str(len(rendered_html))+" bytes)..."+RENDERED_PATH+TEMPLATE_NAME)
    with open(RENDERED_PATH+TEMPLATE_NAME, "w") as text_file:
       text_file.write(rendered_html)


if __name__ == "__main__":
    print("running app.run...")
    save_data()
