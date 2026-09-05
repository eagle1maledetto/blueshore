# Installing Blueshore

All commands run on the Zimbra mailbox server. `SKIN` stands for the variant
you are installing: `blueshoretide`, `blueshoretidedark`, `blueshoresand` or
`blueshoresanddark`. Repeat the steps for every variant you want to offer.

Paths below are the defaults of a Zimbra 10 installation
(`/opt/zimbra/jetty_base/webapps/zimbra/skins`).

## 1. Get the skin

Prebuilt skins are attached to every release on
<https://github.com/eagle1maledetto/blueshore/releases>, two archives per
variant with the same content: `<SKIN>-<version>.zip`, the format
`zmskindeploy` takes directly, and `<SKIN>-<version>.tar.gz`. Both hold a
single `<SKIN>/` directory.

`zmskindeploy` names the skin after the zip file, so save the download as
`<SKIN>.zip`:

```sh
VER=1.0.2
SKIN=blueshoretide
curl -fLo /tmp/$SKIN.zip https://github.com/eagle1maledetto/blueshore/releases/download/v$VER/$SKIN-$VER.zip
```

Alternatively build from a source checkout (`python3 tools/build.py --all`,
see *How to build* in the [README](README.md)): the result is the same
directory, under `skins/$SKIN`, and `zmskindeploy` accepts it in place of
the zip.

## 2. Deploy

Zimbra 10.1 hardens the webapp directories: `zmacl enable`, run at install
time, makes the whole `/opt/zimbra/jetty/webapps/` tree read-only for the
`zimbra` user through ACLs. `zmskindeploy` knows nothing about that: run as
`zimbra` with the ACLs in place it stops with `Failed to create ...` on a new
skin, but on an update, or on a zip, it fails silently and still prints
`successfully installed`. Either lift the ACLs for the deploy or put the
files in place as root.

### As zimbra, lifting the ACLs

`zmacl disable` removes the ACLs from the whole webapps tree, `zmacl enable`
puts them back: run both, or the web client directories stay writable.
Zimbra's script has no user check and works as `zimbra` on a stock
installation, where everything under webapps belongs to `zimbra`.

```sh
sudo su - zimbra
SKIN=blueshoretide
zmacl disable
zmskindeploy /tmp/$SKIN.zip      # from a source checkout: zmskindeploy /path/to/skins/$SKIN
zmprov fc skin
zmacl enable
```

`zmskindeploy` unpacks the zip (or copies the directory) into
`/opt/zimbra/jetty_base/webapps/zimbra/skins/$SKIN`, replacing an existing
copy, and registers the name in `zimbraInstalledSkin`. It does not flush the
skin cache, hence the `zmprov fc skin`. If `setfacl` is not installed `zmacl`
exits without doing anything; on a build without `zmacl` the directories are
not hardened and the two `zmacl` lines can be skipped.

### As root, leaving the ACLs alone

Put the directory in place as root, hand it to `zimbra`, then register it:

```sh
tar -xzf $SKIN-$VER.tar.gz -C /opt/zimbra/jetty_base/webapps/zimbra/skins/
# from a source checkout: cp -a skins/$SKIN /opt/zimbra/jetty_base/webapps/zimbra/skins/
chown -R zimbra:zimbra /opt/zimbra/jetty_base/webapps/zimbra/skins/$SKIN
su - zimbra -c "zmskindeploy /opt/zimbra/jetty_base/webapps/zimbra/skins/$SKIN; zmprov fc skin"
```

Run on the directory already in place, `zmskindeploy` only registers the
skin (`zimbraInstalledSkin`).

## 3. Offer it to users

Which themes an account may choose is `zimbraAvailableSkin`, read from the
account, then its class of service, then its domain. When it is unset at
every level, the admin console's *Do not limit Themes available to users in
this COS*, every installed skin is offered and there is nothing to do: after
the cache flush the skin is in *Preferences → General → Theme*. Check the
class of service first:

```sh
zmprov gc default zimbraAvailableSkin
```

An empty answer means no limit. **Do not add the skin to a class of service
that returns nothing**: the first value turns "any installed theme" into
"only these", and every other skin disappears from the theme picker of those
users.

If the class of service does limit themes, add the skin to its list, in the
admin console (*Configure → Class of Service → default → Themes*, tick the
skin) or on the command line, where `+` appends to the existing values:

```sh
zmprov mc default +zimbraAvailableSkin $SKIN
zmprov fc skin
```

To make it the default theme for new sessions of that class of service:

```sh
zmprov mc default zimbraPrefSkin $SKIN
```

Per-account enabling is possible with `zmprov ma user@example.com
+zimbraAvailableSkin $SKIN`, but note that an account-level value **replaces**
the COS list instead of adding to it: list every skin that account should see
in the same command (`zmprov ma user@example.com zimbraAvailableSkin a
zimbraAvailableSkin b ...`).

## 4. Verify

The aggregated stylesheet can be checked without logging in:

```sh
curl -sk "https://mail.example.com/css/skin.css?skin=$SKIN" | wc -c
```

About 180 KB and containing `Public Sans` means the skin is served. About
24 KB means Zimbra fell back to the default skin: the registration has not
been picked up yet. Restart the web client once:

```sh
su - zimbra -c 'zmmailboxdctl restart'
```

and check again. Then log in, open *Preferences → General → Theme* and pick
the skin.

Skin names must be plain ASCII letters and digits: the CSS servlet strips any
other character from the `skin` parameter before resolving it, and a name
such as `blue-shore` silently becomes `blueshore`, which does not exist, so the
default skin is served with no error in the logs. The names shipped here are
safe; keep the rule if you make your own variant.

## Updating

Deploy the new version the same way as the first one: `zmskindeploy` on a
zip, or on a directory outside `skins/`, replaces the installed copy (as
`zimbra`, between `zmacl disable` and `zmacl enable`). As root, unpack over
the installed directory instead:

```sh
tar -xzf $SKIN-$VER.tar.gz -C /opt/zimbra/jetty_base/webapps/zimbra/skins/
# from a source checkout: cp -a skins/$SKIN/. /opt/zimbra/jetty_base/webapps/zimbra/skins/$SKIN/
chown -R zimbra:zimbra /opt/zimbra/jetty_base/webapps/zimbra/skins/$SKIN
su - zimbra -c 'zmprov fc skin'
```

Either way finish with `zmprov fc skin`. No restart is needed, also for
changes to `manifest.xml`.

Browsers cache the aggregated CSS for 30 days and the cache key is the Zimbra
build version, which does not change when skin files do. Users who still see
the old look need a hard reload (Ctrl+F5 / Cmd+Shift+R) or a new browser
session.

## Removing

```sh
rm -rf /opt/zimbra/jetty_base/webapps/zimbra/skins/$SKIN
su - zimbra -c "zmprov mcf -zimbraInstalledSkin $SKIN; zmprov fc skin"
```

If the skin had been added to the list of a class of service or an account,
remove it there too (`zmprov mc default -zimbraAvailableSkin $SKIN`).
Accounts whose `zimbraPrefSkin` still points to the removed skin fall back to
the default skin on next login.

## Domain theme colours

Zimbra lets a domain force four theme colours (`zimbraSkinBackgroundColor`,
`zimbraSkinForegroundColor`, `zimbraSkinSecondaryColor`,
`zimbraSkinSelectionColor`). When set, the CSS servlet substitutes them into
every skin, Blueshore included, and the palette is lost (surfaces take the
domain background colour). Check and clear them:

```sh
zmprov gd example.com zimbraSkinBackgroundColor zimbraSkinForegroundColor zimbraSkinSecondaryColor zimbraSkinSelectionColor
zmprov md example.com zimbraSkinBackgroundColor '' zimbraSkinForegroundColor '' zimbraSkinSecondaryColor '' zimbraSkinSelectionColor ''
zmprov fc skin
```

## Logo

Blueshore does not ship a logo: it shows whatever the domain is configured
for, exactly like the stock skins. The banner in the top-left corner and the
link it points to are domain attributes:

```sh
zmprov md example.com zimbraSkinLogoAppBanner https://example.com/logo.png zimbraSkinLogoURL https://example.com
```

The same image is used by every skin of the domain, light and dark alike.
The logo licensing rules of Zimbra (see the note at the top of
`skin.properties`) apply as with any other skin.

## Troubleshooting

- **White page after login for accounts on the skin.** `img/images.css.js` is
  missing from the skin directory: the shell JSP needs it. Unpack or copy
  the whole `<SKIN>` directory again.
- **Empty folder tree, no errors in the console.** An image used by the
  coloured-icon compositing failed to load; copy the directory again and
  flush.
- **The CSS endpoint returns HTTP 500.** The server-side CSS generator
  rejects some modern selectors; this cannot happen with the shipped files,
  but if you edit `skin.css` test the endpoint after every change.
- **Theme shows the right name but looks like the default skin.** See
  "Verify" above (registration not picked up) or "Domain theme colours".
- **`zmskindeploy` says "successfully installed" but nothing changed.** It
  was run as `zimbra` with the ACLs in place (see "Deploy"): the copy failed
  silently. Run `zmacl disable` first, or put the files in place as root.
