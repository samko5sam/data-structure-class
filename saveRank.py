import os
import json
import yaml
from datetime import date
from lib.getRanking import get_ranking

def save_rankings_to_file(rankings, filename="rankings.json"):
    today = date.today().strftime("%Y-%m-%d")
    filepath = os.path.join(os.getcwd(), filename)

    # Load existing data if the file exists
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding="utf-8") as f:
            try:
                all_rankings = json.load(f)
            except json.JSONDecodeError:
                all_rankings = {}
    else:
        all_rankings = {}

    # Add/Overwrite today's rankings
    all_rankings[today] = rankings

    # Write the updated data back to the file
    with open(filepath, 'w', encoding="utf-8") as f:
        json.dump(all_rankings, f, indent=4)

if __name__ == "__main__":
    try:
        # Read app data from apps.yaml
        with open("apps.yaml", 'r', encoding="utf-8") as yaml_file:
            app_data = yaml.safe_load(yaml_file)

        # Extract app URLs and IDs
        rankings = {}
        app_urls = []
        for app in app_data['apps']:
            app_id = app['id']
            regions = app['regions']
            for region in regions:
                if ('ios' in app) and app['ios']['id']:
                    app_urls.append(f"https://app.sensortower.com/overview/{app['ios']['id']}?country={region}")
                if ('android' in app) and app['android']['id']:
                    app_urls.append(f"https://app.sensortower.com/overview/{app['android']['id']}?country={region}")

        # Get rankings for each app and region
        if app_urls:
            app_rankings = get_ranking(app_urls)
            index = 0
            for app in app_data['apps']:
                app_id = app['id']
                regions = app['regions']
                for region in regions:
                    if ('ios' in app):
                        rankings[f"{app_id}_{region.lower()}_ios"] = {key: app_rankings[index][key] for key in ['rank', 'category']}
                        index += 1
                    if ('android' in app):
                        rankings[f"{app_id}_{region.lower()}_android"] = {key: app_rankings[index][key] for key in ['rank', 'category']}
                        index += 1

        print(f"Today's rankings: {rankings}")
        save_rankings_to_file(rankings)
        print("Rankings saved to rankings.json")
    except Exception as e:
        print(f"An error occurred: {e}")
