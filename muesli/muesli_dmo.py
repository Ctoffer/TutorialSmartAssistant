import util.config
from muesli.api import MuesliSession

muesli_account = util.config.load_config("../account_data.json").muesli

with MuesliSession(account=muesli_account) as session:
    my_tutorials = session.get_my_tutorials()
    print(my_tutorials)