import logging

from ca.models import CampusAmbassador
from makeaton.models import TeamMember

logger = logging.getLogger('home')


def cross_match_referrals():
    for ca in CampusAmbassador.objects.all():
        if TeamMember.objects.filter(coupon_code=ca.coupon_code, referral__isnull=True).exists():
            TeamMember.objects.filter(coupon_code=ca.coupon_code, referral__isnull=True).update(referral=ca)
            logger.info(
                f"Matched {ca} to {TeamMember.objects.filter(coupon_code=ca.coupon_code, referral__isnull=True)}")


import requests


def has_user_starred_repo(username, repo_owner="conductor-oss", repo_name="conductor"):
    """
    Check if a GitHub user has starred a specific repository.

    :param username: GitHub username of the user
    :param repo_owner: Owner of the repository
    :param repo_name: Name of the repository
    :return: True if the user has starred the repo, False otherwise
    """
    # GitHub API URL to get the list of starred repos for the user
    url = f"https://api.github.com/users/{username}/starred"

    # Make a GET request to the API
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the JSON response
        starred_repos = response.json()

        # Loop through the repos to check if the specific repo exists
        for repo in starred_repos:
            if repo['owner']['login'] == repo_owner and repo['name'] == repo_name:
                return True

        return False  # Repo not found in the starred list
    else:
        raise Exception(f"Failed to fetch starred repos: {response.status_code}")


def bulk_started_status_check(queryset):
    """
    Check the started status of participants in bulk.

    :param queryset: Queryset of TeamMember objects
    :return: Dictionary of participant IDs and their started status
    """

    for team_member in queryset:
        user_name = None
        try:
            user_name = team_member.github_profile.split('/')[-1].strip().strip('/').strip()
            if user_name:
                team_member.started_conductor = has_user_starred_repo(user_name)
                team_member.save()
                logger.info(f"Updated started status for {team_member}")
        except Exception as e:
            logger.error(f"Error updating started status for {team_member}: {e},{user_name}, {team_member.github_profile}")
            continue
