from tqdm import tqdm

from . import delay, limits


def unfollow(self, user_id):
    user_id = self.convert_to_user_id(user_id)
    user_info = self.get_user_info(user_id)
    username = user_info["username"]
    self.console_print('===> Going to unfollow `user_id`: {} with username: {}'.format(user_id, username))

    if self.check_user(user_id, unfollowing=True):
        return True  # whitelisted user
    if limits.check_if_bot_can_unfollow(self):
        delay.unfollow_delay(self)
        if self.api.unfollow(user_id):
            msg = '===> Unfollowed, `user_id`: {}, user_name: {}'
            self.console_print(msg.format(user_id, username), 'yellow')
            self.total_unfollowed += 1
            return True
    else:
        self.logger.info("Out of unfollows for today.")
    return False


def unfollow_users(self, user_ids):
    broken_items = []
    self.logger.info("Going to unfollow {} users.".format(len(user_ids)))
    user_ids = set(map(str, user_ids))
    filtered_user_ids = list(set(user_ids) - set(self.whitelist))
    if len(filtered_user_ids) != len(user_ids):
        self.logger.info(
            "After filtration by whitelist {} users left.".format(len(filtered_user_ids)))
    for user_id in tqdm(filtered_user_ids, desc='Processed users'):
        if not self.unfollow(user_id):
            delay.error_delay(self)
            i = filtered_user_ids.index(user_id)
            broken_items = filtered_user_ids[i:]
            break
    self.logger.info("DONE: Total unfollowed {} users.".format(self.total_unfollowed))
    return broken_items


def unfollow_non_followers(self, n_to_unfollows=None):
    self.logger.info("Unfollowing non-followers.")
    self.update_unfollow_file()
    self.console_print(" ===> Start unfollowing non-followers <===", 'red')

    unfollows = utils.file("unfollowed.txt").list
    for user_id in tqdm(unfollows[:n_to_unfollows]):
        self.unfollow(user_id)
    self.console_print(" ===> Unfollow non-followers done! <===", 'red')


def unfollow_everyone(self):
    self.unfollow_users(self.following)


def update_unfollow_file(self):
    self.logger.info("Updating `unfollowed.txt`.")
    self.console_print("Calculating non-followers list.", 'green')

    followings = set(self.following)
    followers = set(self.followers)
    friends = utils.file("friends.txt").set  # same whitelist (just user ids)
    followed = utils.file("followed.txt").set
    non_followers = followings - followers - friends
    unfollow = non_followers & followed
    unfollow.update(non_followers - followed)

    unfollowed = utils.file("unfollowed.txt")
    new_unfollow = unfollowed.set & unfollow
    new_unfollow.update(unfollow - unfollowed.set)
    unfollowed.save_list(new_unfollow)
