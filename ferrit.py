import os
import sys
import json
import requests
import git
import urllib3
from urllib.parse import urlparse
from pkg_resources import (
    get_distribution,
    DistributionNotFound,
    RequirementParseError,
)


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    __version__ = get_distribution(__name__).version
except (DistributionNotFound, RequirementParseError):
    __version__ = None


class Ferrit:
    SSL_VERIFY = False
    REMOTE_NAME = "origin"
    RES_START = ")]}'\n"

    def __init__(self):
        self._user_name_map = None

    def setup(self):
        try:
            self.repo = git.Repo(search_parent_directories=True)
        except git.exc.InvalidGitRepositoryError:
            self.crash("Not a git repo")

        try:
            self.remote = self.repo.remotes[self.REMOTE_NAME]
        except IndexError:
            self.crash("Remote {} not found".format(self.REMOTE_NAME))

        o = urlparse(self.remote.url)

        if not o.path.startswith("/a/"):
            self.crash("Unexpected remote url format (not a gerrit remote?)")

        self.repo_name = o.path[len("/a/"):]

        try:
            gerrit_user, gerrit_addr = o.netloc.split("@")
        except ValueError:
            gerrit_user = None
            gerrit_addr = o.netloc

        with open(os.path.expanduser("~/.git-credentials"), "r") as f:
            credentialss = [line.strip() for line in f.readlines()]

        for credentials in credentialss:
            o = urlparse(credentials)
            c_userpass, c_addr = o.netloc.split("@")
            c_user = c_userpass.split(":")[0]
            if c_addr == gerrit_addr:
                if gerrit_user is not None and c_user != gerrit_user:
                    continue
                else:
                    break
        else:
            self.crash("No credentials found")

        self.api_base_url = credentials
        self.api_base_url += "/a/"

        repo_dir = self.repo.common_dir
        os.chdir(repo_dir)

    def run(self):
        args = sys.argv[1:]

        if args:
            if args[0] == "--version":
                print("Ferrit v" + __version__)
                self.quit()

        self.setup()

        if args:
            try:
                change_num = int(args[0])
            except ValueError:
                pass
            else:
                if len(args) == 1:
                    self.run_checkout_patch_set(change_num)
                elif len(args) == 2:
                    try:
                        patch_set_num = int(args[1])
                    except ValueError:
                        self.crash("Invalid arguments")
                    else:
                        self.run_checkout_patch_set(change_num, patch_set_num)
                else:
                    self.crash("Invalid arguments")

                self.quit()

            self.run_search(args)
        else:
            self.run_list_changes()

    def run_checkout_patch_set(self, change_num, patch_set_num=None):
        path = "changes/{}/?o=ALL_REVISIONS".format(change_num)
        change = self.api_get(path)

        if change is None:
            self.crash("Change not found")

        patch_sets = self.get_ordered_patch_sets(change)

        if patch_set_num is None:
            patch_set = patch_sets[-1]
        else:
            try:
                patch_set = patch_sets[patch_set_num - 1]
            except IndexError:
                self.crash("Patch set not found")

        print()
        self.print_change(change)
        print()

        self.fetch_and_checkout(patch_set)

    def fetch_and_checkout(self, patch_set):
        fetch_info = patch_set["fetch"]["http"]

        if fetch_info["url"] != self.remote.url:
            self.crash("Fetch url mismatch")

        if self.repo.is_dirty():
            a = self.yn_question("Repo is dirty, continue?")
            if not a:
                self.quit()

        self.remote.fetch(fetch_info["ref"])
        self.repo.git.checkout("FETCH_HEAD")

    def run_search(self, args):
        qs = ["status:open"] + args
        changes = self.api_get_changes(qs)

        if len(changes) == 0:
            print("No changes")
        else:
            print()
            self.print_changes(changes)
            print()

            suggested_change = changes[0]
            default = len(changes) == 1

            if default:
                do_checkout = self.yn_question("Checkout?", True)
            else:
                q = "Checkout change {}?".format(suggested_change["_number"])
                do_checkout = self.yn_question(q, False)

            if do_checkout:
                patch_set = self.get_ordered_patch_sets(suggested_change)[-1]
                self.fetch_and_checkout(patch_set)

    def run_list_changes(self):
        base_qs = ["status:open", "-is:ignored"]
        querys = [
            ("Private", ["owner:self", "is:private"]),
            ("WIP", ["owner:self", "is:wip", "-is:private"]),
            ("Open", ["owner:self", "-is:wip", "-is:private"]),
            ("Others", [
                "-owner:self",
                "(reviewer:self+OR+assignee:self+OR+cc:self)"
            ]),
        ]

        print()

        for label, qs in querys:
            changes = self.api_get_changes(base_qs + qs)

            print(label + ":")

            if changes:
                self.print_changes(changes)
            else:
                print("  No changes found")

            print()

    def print_change(self, change):
        num = change["_number"]
        wip = change.get("work_in_progress", False)
        private = change.get("is_private", False)

        patch_sets = self.get_number_of_patch_sets(change)

        if wip or private:
            merge_symbol = "-"
        elif change.get("mergeable"):
            merge_symbol = " "
        else:
            merge_symbol = "M"

        owner_name = self.user_name_map[change["owner"]["_account_id"]]

        shown_subject = change["subject"]

        if len(shown_subject) > 54:
            shown_subject = shown_subject[:50] + " ..."

        s = "{n:5} {k:3}  {p} {w} {m}  {o:<3} {s}".format(
                n=num,
                k=patch_sets,
                w=("W" if wip else " "),
                p=("P" if private else " "),
                m=merge_symbol,
                o=owner_name,
                s=shown_subject,
                )

        print(s)

    def print_changes(self, changes):
        for change in changes:
            self.print_change(change)

    def api_get(self, path):
        if path.startswith("/"):
            path = path[1:]

        url = self.api_base_url + path
        r = requests.get(url, verify=self.SSL_VERIFY)

        if r.status_code == 200:
            pass
        elif r.status_code == 404:
            return None
        else:
            self.crash("Bad response: {} ({})".format(r.status_code, r.text))

        assert r.text.startswith(self.RES_START)
        return json.loads(r.text[len(self.RES_START):])

    def api_get_changes(self, qs):
        qs.append("repo:" + self.repo_name)
        qs = list(set(qs))
        path = "changes/?o=ALL_REVISIONS&q=" + "+".join(qs)
        return self.api_get(path)

    def get_ordered_patch_sets(self, change):
        patch_sets = list(change["revisions"].values())
        patch_sets.sort(key=lambda ps: ps["_number"])
        return patch_sets

    def get_number_of_patch_sets(self, change):
        return len(self.get_ordered_patch_sets(change))

    @property
    def user_name_map(self):
        if self._user_name_map is None:
            self._user_name_map = self.api_get_user_name_map()
        return self._user_name_map

    def api_get_user_name_map(self):
        r = self.api_get("accounts/?o=DETAILS&q=is:active")
        user_map = {d["_account_id"]: self.initials(d["name"]) for d in r}
        return user_map

    def initials(self, s):
        s = s.strip().upper().replace("-", " ")
        ws = s.split()
        return "".join([w[0] for w in ws])

    def yn_question(self, msg, default=False):
        suffix = "Y/n" if default else "y/N"
        suffix = " [{}] ".format(suffix)

        try:
            inp = input(msg + suffix).strip().lower()
        except KeyboardInterrupt:
            print()
            self.quit()

        if inp:
            return "yes".startswith(inp)
        else:
            return default

    def quit(self):
        sys.exit(0)

    def crash(self, msg):
        sys.stderr.write(str(msg) + "\n")
        sys.exit(1)


def main():
    Ferrit().run()


if __name__ == "__main__":
    main()
