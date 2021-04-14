from enum import Enum


class AllowDMsFrom(Enum):
    friends_and_members: 'friendsAndServerMembers'
    members: 'friendsAndServerMembers'
    friends: 'friendsOnly'
    everyone: 'everyone'

    def __str__(self):
        return self.value

class AllowFriendRequestsFrom(Enum):
    friends_and_members: 'friendsAndServerMembers'
    members: 'serverMembersOnly'
    everyone: 'everyone'

    def __str__(self):
        return self.value
