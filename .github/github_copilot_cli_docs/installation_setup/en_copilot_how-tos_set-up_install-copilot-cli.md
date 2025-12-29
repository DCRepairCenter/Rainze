# Source: https://docs.github.com/en/copilot/how-tos/set-up/install-copilot-cli

# Downloaded: 2025-12-19 18:43:41

---

# Installing GitHub Copilot CLI

Learn how to install Copilot CLI so that you can use Copilot directly from the command line.

## In this article

* [Prerequisites](#prerequisites)
* [Installing or updating Copilot CLI](#installing-or-updating-copilot-cli)
* [Authenticating with Copilot CLI](#authenticating-with-copilot-cli)
* [Next steps](#next-steps)

Note

GitHub Copilot CLI is in public preview with [data protection](https://gh.io/dpa) and subject to change.

To find out about Copilot CLI before you install it, see [About GitHub Copilot CLI](/en/copilot/concepts/agents/about-copilot-cli).

## [Prerequisites](#prerequisites)

* **An active GitHub Copilot subscription**. See [Copilot plans](https://github.com/features/copilot/plans?ref_product=copilot&ref_type=engagement&ref_style=text).
* (On Windows) **PowerShell** v6 or higher

If you have access to GitHub Copilot via your organization or enterprise, you cannot use Copilot CLI if your organization owner or enterprise administrator has disabled it in the organization or enterprise settings. See [Managing policies and features for GitHub Copilot in your organization](/en/copilot/managing-copilot/managing-github-copilot-in-your-organization/managing-github-copilot-features-in-your-organization/managing-policies-for-copilot-in-your-organization).

## [Installing or updating Copilot CLI](#installing-or-updating-copilot-cli)

You can install Copilot CLI using WinGet (Windows), Homebrew (macOS and Linux), npm (all platforms), or an install script (macOS and Linux).

### [Installing with WinGet (Windows)](#installing-with-winget-windows)

PowerShell

```
winget install GitHub.Copilot
```

```
winget install GitHub.Copilot
```

To install the prerelease version:

PowerShell

```
winget install GitHub.Copilot.Prerelease
```

```
winget install GitHub.Copilot.Prerelease
```

### [Installing with Homebrew (macOS and Linux)](#installing-with-homebrew-macos-and-linux)

Shell

```
brew install copilot-cli
```

```
brew install copilot-cli
```

To install the prerelease version:

Shell

```
brew install copilot-cli@prerelease
```

```
brew install copilot-cli@prerelease
```

### [Installing with npm (all platforms, requires Node.js 22+)](#installing-with-npm-all-platforms-requires-nodejs-22)

Shell

```
npm install -g @github/copilot
```

```
npm install -g @github/copilot
```

To install the prerelease version:

Shell

```
npm install -g @github/copilot@prerelease
```

```
npm install -g @github/copilot@prerelease
```

### [Installing with the install script (macOS and Linux)](#installing-with-the-install-script-macos-and-linux)

Shell

```
curl -fsSL https://gh.io/copilot-install | bash
```

```
curl -fsSL https://gh.io/copilot-install | bash
```

Or:

Shell

```
wget -qO- https://gh.io/copilot-install | bash
```

```
wget -qO- https://gh.io/copilot-install | bash
```

To run as root and install to `/usr/local/bin`, use `| sudo bash`.

To install to a custom directory, set the `PREFIX` environment variable. It defaults to `/usr/local` when run as root or `$HOME/.local` when run as a non-root user.

To install a specific version, set the `VERSION` environment variable. It defaults to the latest version.

For example, to install version `v0.0.369` to a custom directory:

Shell

```
curl -fsSL https://gh.io/copilot-install | VERSION="v0.0.369" PREFIX="$HOME/custom" bash
```

```
curl -fsSL https://gh.io/copilot-install | VERSION="v0.0.369" PREFIX="$HOME/custom" bash
```

### [Download from GitHub.com](#download-from-githubcom)

You can download the executables directly from [the `copilot-cli` repository](https://github.com/github/copilot-cli/releases/).

Download the executable for your platform, unpack it, and run.

## [Authenticating with Copilot CLI](#authenticating-with-copilot-cli)

On first launch, if you're not currently logged in to GitHub, you'll be prompted to use the `/login` slash command. Enter this command and follow the on-screen instructions to authenticate.

### [Authenticating with a personal access token](#authenticating-with-a-personal-access-token)

You can also authenticate using a fine-grained personal access token with the "Copilot Requests" permission enabled.

1. Visit [Fine-grained personal access tokens](https://github.com/settings/personal-access-tokens/new).
2. Under "Permissions," click **Add permissions** and select **Copilot Requests**.
3. Click **Generate token**.
4. Add the token to your environment using the `GH_TOKEN` or `GITHUB_TOKEN` environment variable (in order of precedence).

## [Next steps](#next-steps)

You can now use Copilot from the command line. See [Using GitHub Copilot CLI](/en/copilot/how-tos/use-copilot-agents/use-copilot-cli).

## Help and support

### Did you find what you needed?

Yes No

[Privacy policy](/en/site-policy/privacy-policies/github-privacy-statement)

### Help us make these docs great!

All GitHub docs are open source. See something that's wrong or unclear? Submit a pull request.

[Make a contribution](https://github.com/github/docs/blob/main/content/copilot/how-tos/set-up/install-copilot-cli.md)

[Learn how to contribute](/contributing)

### Still need help?

[Ask the GitHub community](https://github.com/orgs/community/discussions)

[Contact support](https://support.github.com)

## Legal

* © 2025 GitHub, Inc.
* [Terms](/en/site-policy/github-terms/github-terms-of-service)
* [Privacy](/en/site-policy/privacy-policies/github-privacy-statement)
* [Status](https://www.githubstatus.com/)
* [Pricing](https://github.com/pricing)
* [Expert services](https://services.github.com)
* [Blog](https://github.blog)
