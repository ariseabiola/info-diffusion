from collections import ChainMap, Counter

import numpy as np
import pandas as pd
import progressbar


def get_user_published_tweets(user_id, node_collection):
    """notation 6"""
    # all_tweets = {}

    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    tweets = attr['tweets']
    # all_tweets.update(tweets)

    retweeted_tweets = attr['retweeted_tweets']
    # all_tweets.update(retweeted_tweets)

    quoted_tweets = attr['quoted_tweets']
    # all_tweets.update(quoted_tweets)

    return ChainMap(tweets, retweeted_tweets, quoted_tweets)


def get_activity_index(user_id, node_collection, e=30.4*24):
    number_of_user_messages = len(get_user_published_tweets(user_id,
                                                            node_collection))

    if number_of_user_messages < e:
        return number_of_user_messages / e
    else:
        return 1


def users_ever_mentioned(user_id, node_collection):  # get_users_mentioned_in
    """notation 7"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['users_mentioned_in_all_my_tweets']


def get_h(src_user, dest_user, node_collection):
    src_user_mv = users_ever_mentioned(src_user, node_collection)
    dest_user_mv = users_ever_mentioned(dest_user, node_collection)

    x = src_user_mv.intersection(dest_user_mv)
    y = src_user_mv.union(dest_user_mv)

    if len(y):
        return len(x) / len(y)
    else:
        return 0


def tweets_with_user_mentions(user_id, node_collection):
    all_tweets_by_user = get_user_published_tweets(user_id, node_collection)
    return [tweet_id for tweet_id, tweetObj in all_tweets_by_user.items()
            if tweetObj.users_mentioned]


def get_dTR(user_id, node_collection):
    # change dv..... mv is okay
    dv = tweets_with_user_mentions(user_id, node_collection)
    mv = get_user_published_tweets(user_id, node_collection)

    if len(mv) > 0:
        return len(dv) / len(mv)
    else:
        return 0


def get_hM(user_id, user_y, node_collection):
    mvx = users_ever_mentioned(user_id, node_collection)

    if user_y in mvx:
        return 1
    else:
        return 0


def tweets_mentioned_in(user_id, node_collection):
    """notation 9"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['mentioned_in']


def get_mR(user_id, node_collection, meu=200):
    tmv = tweets_mentioned_in(user_id, node_collection)

    if len(tmv) < meu:
        return len(tmv) / meu
    else:
        return 1


def get_keywords_from_user_tweets(user_id, node_collection):
    """notation 12"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['keywords_in_all_my_tweets']


def get_hK(user_id, keywords, node_collection):
    user_tweets_keywords = get_keywords_from_user_tweets(user_id,
                                                         node_collection)

    if not keywords.isdisjoint(user_tweets_keywords):
        return 1
    else:
        return 0


def get_A(user_id, node_collection, hour=None):

    tweet_freq_table = {}

    user_messages = get_user_published_tweets(user_id, node_collection)
    N = len(user_messages)

    if user_messages:
        for _, tweet in user_messages.items():
            tweet_date_and_time = tweet.created_at
            tweet_date = tweet_date_and_time.date
            tweet_hour = tweet_date_and_time.hour
            hour_bin = tweet_hour // 4

            tweet_freq_table.setdefault(
                tweet_date, {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            )[hour_bin] += 1

        results = pd.DataFrame(list(tweet_freq_table.values()))
        results = results / N
        results = results.values
        sum_ = np.sum(results, axis=0)
        # return sum_[hour // 4]
        return sum_
    else:
        return 0


def get_y(src, dest, node_collection):
    """checks whether there's a diffusion from src to dest

    Arguments:
        src {[type]} -- [description]
        dest {[type]} -- [description]

    Returns:
        int -- return 1 if diffusion exists, else 0
    """
    query = {'_id': dest}
    attr = node_collection.find_one(query)

    if src in attr['all_possible_original_tweet_owners']:
        return 1
    else:
        return 0


def generate_default_attr(src_user, dest_user, keywords, node_collection):
    return {
        'src_user_id': src_user,
        'dest_user_id': dest_user,
        'src_I': get_activity_index(src_user, node_collection),
        'dest_I': get_activity_index(dest_user, node_collection),
        'H': get_h(src_user, dest_user, node_collection),
        'src_dTR': get_dTR(src_user, node_collection),
        'dest_dTR': get_dTR(dest_user, node_collection),
        'src_hM': get_hM(src_user, dest_user, node_collection),
        'dest_hM': get_hM(dest_user, src_user, node_collection),
        'src_mR': get_mR(src_user, node_collection),
        'dest_mR': get_mR(dest_user, node_collection),
        'src_hK': get_hK(src_user, keywords, node_collection),
        'dest_hK': get_hK(dest_user, keywords, node_collection),
        'src_A_1': get_A(src_user, node_collection)[0],
        'dest_A_1': get_A(dest_user, node_collection)[0],
        'src_A_2': get_A(src_user, node_collection)[1],
        'dest_A_2': get_A(dest_user, node_collection)[1],
        'src_A_3': get_A(src_user, node_collection)[2],
        'dest_A_3': get_A(dest_user, node_collection)[2],
        'src_A_4': get_A(src_user, node_collection)[3],
        'dest_A_4': get_A(dest_user, node_collection)[3],
        'src_A_5': get_A(src_user, node_collection)[4],
        'dest_A_5': get_A(dest_user, node_collection)[4],
        'src_A_6': get_A(src_user, node_collection)[5],
        'dest_A_6': get_A(dest_user, node_collection)[5],
        'y': get_y(src_user, dest_user, node_collection)
    }


def generate_additional_attr(user_id, keywords, node_collection, user='src',
                             n_days=30):
    return {
        f'{user}_ratio_of_retweets_to_tweets':
        ratio_of_retweets_to_tweets(user_id, node_collection),
        f'{user}_avg_number_of_tweets_with_hastags':
        avg_number_of_tweets_with_hastags(user_id, node_collection),
        f'{user}_avg_number_of_retweets_with_hastags':
        avg_number_of_retweets_with_hastags(user_id, node_collection),
        f'{user}_avg_number_of_retweets':
        avg_number_of_retweets(user_id, node_collection),
        f'{user}_avg_number_of_tweets':
        avg_number_of_tweets(user_id, node_collection),
        f'{user}_avg_number_of_mentions_not_including_retweets':
        avg_number_of_mentions_not_including_retweets(user_id,
                                                      node_collection),
        f'{user}_ratio_of_mentions_to_tweet':
        ratio_of_mentions_to_tweet(user_id, node_collection),
        f'{user}_avg_url_per_retweet':
        avg_url_per_retweet(user_id, node_collection),
        f'{user}_avg_url_per_tweet':
        avg_url_per_tweet(user_id, node_collection),
        f'{user}_avg_number_of_media_in_retweets':
        avg_number_of_media_in_retweets(user_id, node_collection),
        f'{user}_avg_number_of_media_in_tweets':
        avg_number_of_media_in_tweets(user_id, node_collection),
        f'{user}_description':
        description(user_id, node_collection),
        f'{user}_ratio_of_favorited_to_tweet':
        ratio_of_favorited_to_tweet(user_id, node_collection),
        f'{user}_avg_positive_sentiment_of_tweets':
        avg_positive_sentiment_of_tweets(user_id, node_collection),
        f'{user}_avg_negative_sentiment_of_tweets':
        avg_negative_sentiment_of_tweets(user_id, node_collection),
        f'{user}_ratio_of_tweet_per_time_period_1':
        ratio_of_tweet_per_time_period(user_id, node_collection)[1],
        f'{user}_ratio_of_tweet_per_time_period_2':
        ratio_of_tweet_per_time_period(user_id, node_collection)[2],
        f'{user}_ratio_of_tweet_per_time_period_3':
        ratio_of_tweet_per_time_period(user_id, node_collection)[3],
        f'{user}_ratio_of_tweet_per_time_period_4':
        ratio_of_tweet_per_time_period(user_id, node_collection)[4],
        f'{user}_ratio_of_tweets_that_got_retweeted_per_time_period_1':
        ratio_of_tweets_that_got_retweeted_per_time_period(user_id,
                                                           node_collection)[1],
        f'{user}_ratio_of_tweets_that_got_retweeted_per_time_period_2':
        ratio_of_tweets_that_got_retweeted_per_time_period(user_id,
                                                           node_collection)[2],
        f'{user}_ratio_of_tweets_that_got_retweeted_per_time_period_3':
        ratio_of_tweets_that_got_retweeted_per_time_period(user_id,
                                                           node_collection)[3],
        f'{user}_ratio_of_tweets_that_got_retweeted_per_time_period_4':
        ratio_of_tweets_that_got_retweeted_per_time_period(user_id,
                                                           node_collection)[4],
        f'{user}_ratio_of_retweet_per_time_period_1':
        ratio_of_retweet_per_time_period(user_id, node_collection)[1],
        f'{user}_ratio_of_retweet_per_time_period_2':
        ratio_of_retweet_per_time_period(user_id, node_collection)[2],
        f'{user}_ratio_of_retweet_per_time_period_3':
        ratio_of_retweet_per_time_period(user_id, node_collection)[3],
        f'{user}_ratio_of_retweet_per_time_period_4':
        ratio_of_retweet_per_time_period(user_id, node_collection)[4],
        f'{user}_avg_number_followers':
        avg_number_followers(user_id, node_collection),
        f'{user}_avg_number_friends':
        avg_number_friends(user_id, node_collection),
        f'{user}_ratio_of_follower_to_friends':
        ratio_of_follower_to_friends(user_id, node_collection),
    }


def calculate_network_diffusion(edges, keywords, node_collection, *,
                                additional_attr=False,
                                do_not_add_sentiment=False, n_days=30):
    # todo: turn this into a generator and see if its contents will only be
    # consumed once. this will require removing counter and search for another
    # way of knowing the number of things calculated
    # changed results.append to yield

    widgets = ['Building Features, ',
               progressbar.Counter('Processed %(value)03d'),
               ' edges (', progressbar.Timer(), ')']
    bar = progressbar.ProgressBar(widgets=widgets)
    for src_user, dest_user in bar(edges):
        def_result = generate_default_attr(
            src_user, dest_user, keywords, node_collection)

        if additional_attr:
            src_result = generate_additional_attr(
                src_user, keywords, node_collection)
            dest_result = generate_additional_attr(
                dest_user, keywords, node_collection, user='dest')

            result = ChainMap(def_result, src_result, dest_result)
            yield (result)
        else:
            yield (def_result)


def retweeted_tweets(user_id, node_collection):
    """---"""
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['retweeted_tweets']


def retweet_count(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['retweet_count']


def ratio_of_retweets_to_tweets(user_id, node_collection):
    """ notation 7 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    total_number_of_tweets_retweeted = attr['retweeted_count']
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    # todo: might need to check for divisible by zero
    return total_number_of_tweets_retweeted / total_number_of_tweets


def tweets_with_hashtags(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['tweets_with_hashtags']


def avg_number_of_tweets_with_hastags(user_id, node_collection):
    """ notation 8 (ii) (new) """
    total_number_of_tweets_with_hashtags = len(tweets_with_hashtags(
        user_id, node_collection))
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    # todo: might need to check for divisible by zero
    return total_number_of_tweets_with_hashtags / total_number_of_tweets


def retweets_with_hashtags(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['retweeted_tweets_with_hashtags']


def avg_number_of_retweets_with_hastags(user_id, node_collection):
    """ notation 8 (i) (new) """
    n_retweets_with_hashtags = len(retweets_with_hashtags(
        user_id, node_collection))
    n_retweeted_tweets = len(retweeted_tweets(user_id, node_collection))

    # todo: might need to check for divisible by zero
    if n_retweeted_tweets:
        return n_retweets_with_hashtags / n_retweeted_tweets
    else:
        return 0


def avg_number_of_retweets(user_id, node_collection):
    """ number 9 (new) """
    n_retweeted_tweets = len(retweeted_tweets(user_id, node_collection))
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    # todo: might need to check for divisible by zero
    return n_retweeted_tweets / total_number_of_tweets


def get_user_number_of_tweet_days(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    tweet_max_date = attr['tweet_max_date']
    tweet_min_date = attr['tweet_min_date']
    diff = tweet_max_date - tweet_min_date

    return diff.days


def avg_number_of_tweets(user_id, node_collection, n_days=30):
    """ number 10 (new) """
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))
    n_days = get_user_number_of_tweet_days(user_id, node_collection)

    if total_number_of_tweets and n_days == 0:
        n_days = 1

    avg = total_number_of_tweets / n_days

    if avg > 1:
        avg = 1

    return avg


def avg_number_of_mentions_not_including_retweets(user_id, node_collection):
    """ number 11 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    count = attr['tweets_with_others_mentioned_count']
    + attr['quoted_tweets_with_others_mentioned_count']
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    # todo: might need to check for divisible by zero
    return count / total_number_of_tweets


def avg_number_followers(user_id, node_collection):
    """ number 12 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    n_followers = attr['followers_count']

    avg = n_followers / 707

    # bound by 1
    if avg > 1:
        avg = 1

    return avg


def avg_number_friends(user_id, node_collection):
    """ number 13 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    n_friends = attr['friends_count']

    avg = n_friends / 707

    # bound by 1
    if avg > 1:
        avg = 1

    return avg


def avg_number_of_mentions(self):
    """ number 14 (new) """
    pass  # more information is needed


def variance_tweets_per_day(self):
    """ number 15 (new) """
    pass  # more information is needed


def ratio_of_mentions_to_tweet(user_id, node_collection):
    """ number 16 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    all_tweets_with_mentions_count = attr['tweets_with_others_mentioned_count']
    + attr['retweets_with_others_mentioned_count']
    + attr['quoted_tweets_with_others_mentioned_count']

    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    # todo: might need to check for divisible by zero
    return all_tweets_with_mentions_count / total_number_of_tweets


def tweets_with_urls(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['tweets_with_urls']


def retweeted_tweets_with_urls(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['retweeted_tweets_with_urls']


def quoted_tweets_with_urls(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['quoted_tweets_with_urls']


def avg_url_per_retweet(user_id, node_collection):
    """ number 17 (i) new """
    number_of_retweeted_tweets_with_url = len(
        retweeted_tweets_with_urls(user_id, node_collection))
    n_retweeted_tweets = len(retweeted_tweets(user_id, node_collection))

    # todo: might need to check for divisible by zero
    if n_retweeted_tweets:
        return number_of_retweeted_tweets_with_url / n_retweeted_tweets
    else:
        return 0


def avg_url_per_tweet(user_id, node_collection):
    """ number 17 (ii) new """
    number_of_all_tweets_with_url = len(tweets_with_urls(user_id,
                                                         node_collection))
    + len(retweeted_tweets_with_urls(user_id, node_collection))
    # get_quoted_tweets_with_url
    + len(quoted_tweets_with_urls(user_id, node_collection))

    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    # todo: might need to check for divisible by zero
    return number_of_all_tweets_with_url / total_number_of_tweets


def tweets_with_media(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['tweets_with_media']

# get_retweeted_tweets_with_media


def retweeted_tweets_with_media(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['retweeted_tweets_with_media']


def quoted_tweets_with_media(user_id, node_collection):
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    return attr['quoted_tweets_with_media']


def avg_number_of_media_in_retweets(user_id, node_collection):
    """ number 18 (i) new """
    number_of_retweets_with_media = len(
        retweeted_tweets_with_media(user_id, node_collection))
    n_retweeted_tweets = len(retweeted_tweets(user_id, node_collection))

    # todo: might need to check for divisible by zero
    if n_retweeted_tweets:
        return number_of_retweets_with_media / n_retweeted_tweets
    else:
        return 0


def avg_number_of_media_in_tweets(user_id, node_collection):
    """ number 18 (ii) new """
    number_of_all_tweets_with_media = len(tweets_with_media(user_id,
                                                            node_collection))
    # get_retweeted_tweets_with_media + len(quoted_tweets_with_media(self))
    + len(retweeted_tweets_with_media(user_id, node_collection))

    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    # todo: might need to check for divisible by zero
    return number_of_all_tweets_with_media / total_number_of_tweets


def description(user_id, node_collection):
    """ number 19 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)
    if attr['description']:
        return 1
    else:
        return 0


def ratio_of_follower_to_friends(user_id, node_collection):
    """ number 20 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    number_of_followers = len(attr['followers_ids'])
    number_of_friends = len(attr['friends_ids'])

    if number_of_friends == 0:
        return 0

    ratio = number_of_followers / number_of_friends

    if ratio > 1:
        ratio = 1

    return ratio


def ratio_of_favorited_to_tweet(user_id, node_collection):
    """ number 21 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    number_of_favorited_tweets = attr['favorite_tweets_count']
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    return number_of_favorited_tweets / total_number_of_tweets


def avg_time_before_retweet_quote_favorite(self):
    """ number 23 (new) """

    # need more information
    pass


def avg_positive_sentiment_of_tweets(user_id, node_collection):
    """ number 24 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    number_of_positive_sentiments = attr['positive_sentiment_count']
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    return number_of_positive_sentiments / total_number_of_tweets


def avg_negative_sentiment_of_tweets(user_id, node_collection):
    """ number 24 (new) """
    query = {'_id': user_id}
    attr = node_collection.find_one(query)

    number_of_negative_sentiments = attr['negative_sentiment_count']
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    return number_of_negative_sentiments / total_number_of_tweets


def ratio_of_tweet_per_time_period(user_id, node_collection):
    """ separate tweets in 4 periods using the hour attribute

        number 25 (new)
    Arguments:
        user_id {[type]} -- [description]
        node_collection {[type]} -- [description]
    """

    all_user_tweets = get_user_published_tweets(user_id, node_collection)
    total_number_of_tweets = len(all_user_tweets)

    periods = Counter()

    for _, tweet in all_user_tweets.items():
        h = tweet.created_at.hour

        if h in range(0, 24):
            period = h // 6 + 1
            periods[period] += 1

    for key, value in periods.items():
        periods[key] = value / total_number_of_tweets

    return periods


def ratio_of_tweets_that_got_retweeted_per_time_period(user_id,
                                                       node_collection):
    """ separate tweets in 4 periods using the hour attribute

        number 26 (new)
    Arguments:
        user_id {[type]} -- [description]
        node_collection {[type]} -- [description]
    """

    all_user_tweets = retweeted_tweets(user_id, node_collection)
    total_number_of_tweets = len(get_user_published_tweets(user_id,
                                                           node_collection))

    periods = Counter()

    for _, tweet in all_user_tweets.items():
        h = tweet.created_at.hour

        if h in range(0, 24):
            period = h // 6 + 1
            periods[period] += 1

    for key, value in periods.items():
        periods[key] = value / total_number_of_tweets

    return periods


def ratio_of_retweet_per_time_period(user_id, node_collection):
    """ separate tweets in 4 periods using the hour attribute

        number 27 (new)
    Arguments:
        user_id {[type]} -- [description]
        node_collection {[type]} -- [description]
    """

    all_user_tweets = retweeted_tweets(user_id, node_collection)
    total_number_of_tweets = len(all_user_tweets)

    periods = Counter()

    for _, tweet in all_user_tweets.items():
        h = tweet.created_at.hour

        if h in range(0, 24):
            period = h // 6 + 1
            periods[period] += 1

    for key, value in periods.items():
        if total_number_of_tweets:
            periods[key] = value / total_number_of_tweets
        else:
            periods[key] = 0

    return periods
