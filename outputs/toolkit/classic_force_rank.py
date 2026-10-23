"""Original Force-user rank predicates use distinct raw and copied master IDs."""
PADAWAN_COPY=frozenset((180,183,232,204,52,239,647,652))
PADAWAN_RAW=frozenset((1075,1076,800,814,824))
MASTER_COPY=frozenset((115,125,136,134,89,140,643,645))
MASTER_RAW=frozenset((1077,1085,1082,1084,1080,725,728,731,747,753,761,770,778,784,806,792))


def ranks(raw,copy):
    raw=(raw+32768)%65536-32768
    copy=(copy+32768)%65536-32768
    return copy in PADAWAN_COPY or raw in PADAWAN_RAW,copy in MASTER_COPY or raw in MASTER_RAW
