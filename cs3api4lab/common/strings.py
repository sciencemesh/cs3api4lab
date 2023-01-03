class State:
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    INVALID = 'invalid'


class Role:
    VIEWER = 'viewer'
    EDITOR = 'editor'


class Grantee:
    USER = 'user'
    GROUP = 'group'
    INVALID = 'invalid'
