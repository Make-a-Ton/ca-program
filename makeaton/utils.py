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
