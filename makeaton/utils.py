import logging
import re
import time
from urllib.parse import urlparse
import requests
from django.conf import settings
from django.utils import timezone

from base.utils import clean_mobile_number
from ca.models import CampusAmbassador
from makeaton.models import TeamMember

logger = logging.getLogger('home')

RATE_LIMIT_PER_SECOND = 1
RATE_LIMIT_PER_MINUTE = 80  # Maximum allowable requests per minute
REQUEST_DELAY = 1 / RATE_LIMIT_PER_SECOND  # Time to wait between requests (approx. 0.75 sec)


def cross_match_referrals():
    for ca in CampusAmbassador.objects.all():
        if TeamMember.objects.filter(coupon_code=ca.coupon_code, referral__isnull=True).exists():
            TeamMember.objects.filter(coupon_code=ca.coupon_code, referral__isnull=True).update(referral=ca)
            logger.info(
                f"Matched {ca} to {TeamMember.objects.filter(coupon_code=ca.coupon_code, referral__isnull=True)}")


def update_leader_phone_numbers(dataset):
    print("Sleeping for 120 seconds")
    time.sleep(120)
    print("Waking up")
    for data in dataset:
        try:
            phone,leader_phone = clean_mobile_number(data[3]),clean_mobile_number(data[21])
            team_member = TeamMember.objects.get(phone_number=phone)
            if not team_member.leader_phone_number:
                team_member.leader_phone_number = leader_phone
                team_member.save()
            # else:
            #     logger.info(f"Leader phone number already exists for {team_member}")
        except TeamMember.DoesNotExist:
            logger.error(f"Team member with phone number {data[3]} not found")


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
    response = requests.get(url,
                            headers={
                                "Accept": "application/vnd.github.v3+json",
                                "Authorization": f"token {settings.GITHUB_API_TOKEN}"
                            })

    if response.status_code == 200:
        # Parse the JSON response
        starred_repos = response.json()

        # Loop through the repos to check if the specific repo exists
        for repo in starred_repos:
            if repo['owner']['login'] == repo_owner and repo['name'] == repo_name:
                return True

        return False  # Repo not found in the starred list
    if response.status_code == 404:
        return False
    if response.status_code == 403:
        logger.error(f"Rate limit exceeded for {username}")
        raise Exception(f"Rate limit exceeded for {username}")
    else:
        raise Exception(f"Failed to fetch starred repos: {response.status_code}")


# def clean_github(profile):
#     try:
#         # Parse the URL to extract path
#         parsed_url = urlparse(profile)
#
#         # Extract the path (removing any trailing slashes)
#         path = parsed_url.path.strip('/')
#
#         # Split the path and get the last part (the username)
#         username = path.split('/')[-1]
#
#         # Return the cleaned username (remove any surrounding spaces or slashes)
#         return username.strip().strip(".git").strip('.github.io')
#
#     except Exception as e:
#         # Handle any exception and return a meaningful error message or None
#         return None

def clean_github(profile):
    try:
        url = re.sub(r'([^:])//+', r'\1/', profile.strip())

        # Regular expression to match a GitHub profile URL and extract the username
        pattern = r"https?://(www\.)?github\.com/([A-Za-z0-9\-]+)"
        match = re.match(pattern, url.strip())

        if match:
            # Return the captured username from the match
            return match.group(2)
        else:
            # If the URL does not match, return None
            return None
    except Exception as e:
        # Handle any exception and return None
        return None


def bulk_started_status_check(queryset):
    """
    Check the started status of participants in bulk.

    :param queryset: Queryset of TeamMember objects
    :return: Dictionary of participant IDs and their started status
    https://api.github.com/repos/conductor-oss/conductor/stargazers?per_page=100&page=3
    change to this url
    """
    count = 0
    start_time = timezone.now()
    for team_member in queryset:
        user_name = None
        if team_member.last_start_checked and (timezone.now() - team_member.last_start_checked).seconds < 4 * 60 * 60:
            logger.info(f"Skipping {team_member} as it was checked recently")
            continue
        try:
            user_name = clean_github(team_member.github_profile)
            logger.info(f"Checking started status for {team_member}")
            if user_name:
                count += 1
                time.sleep(REQUEST_DELAY)
                if count % RATE_LIMIT_PER_MINUTE == 0:
                    time.sleep(60)
                team_member.starred_conductor = has_user_starred_repo(user_name)
                team_member.last_start_checked = timezone.now()
                team_member.save()
                logger.info(f"Updated started status for {team_member} to {team_member.starred_conductor}")
        except Exception as e:
            logger.error(
                f"Error updating started status for {team_member}: {e},{user_name}, {team_member.github_profile}")
    logger.info(f"Checked {count} participants completed in {(timezone.now() - start_time).seconds // 60} minutes")
