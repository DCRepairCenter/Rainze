# Source: https://docs.github.com/en/copilot/reference/copilot-allowlist-reference

# Downloaded: 2025-12-19 18:43:56

---

# Copilot allowlist reference

Learn how to allow certain traffic through your firewall or proxy server for Copilot to work as intended in your organization.

## Who can use this feature?

Proxy server maintainers or firewall maintainers

## In this article

* [GitHub public URLs](#github-public-urls)
* [Copilot coding agent recommended allowlist](#copilot-coding-agent-recommended-allowlist)
* [Further reading](#further-reading)
* [Footnotes](#footnote-label)

If your company employs security measures like a firewall or proxy server, you should add the following URLs, ports, and protocols to an allowlist to ensure Copilot works as expected:

## [GitHub public URLs](#github-public-urls)

| Domain and/or URL | Purpose |
| --- | --- |
| `https://github.com/login/*` | Authentication |
| `https://github.com/enterprises/YOUR-ENTERPRISE/*` | Authentication for managed user accounts, only required with Enterprise Managed Users |
| `https://api.github.com/user` | User Management |
| `https://api.github.com/copilot_internal/*` | User Management |
| `https://copilot-telemetry.githubusercontent.com/telemetry` | Telemetry |
| `https://collector.github.com/*` | Analytics telemetry |
| `https://default.exp-tas.com` | Telemetry |
| `https://copilot-proxy.githubusercontent.com` | API service for Copilot suggestions |
| `https://origin-tracker.githubusercontent.com` | API service for Copilot suggestions |
| `https://*.githubcopilot.com/*`[1](#user-content-fn-1) | API service for Copilot suggestions |
| `https://*.individual.githubcopilot.com`[2](#user-content-fn-2) | API service for Copilot suggestions |
| `https://*.business.githubcopilot.com`[3](#user-content-fn-3) | API service for Copilot suggestions |
| `https://*.enterprise.githubcopilot.com`[4](#user-content-fn-4) | API service for Copilot suggestions |
| `https://*.SUBDOMAIN.ghe.com` | For Copilot users on GHE.com |
| `https://SUBDOMAIN.ghe.com` | For Copilot users on GHE.com |

Depending on the security policies and editors your organization uses, you may need to allowlist additional domains and URLs. For more information on specific editors, see [Further reading](#further-reading).

Every user of the proxy server or firewall also needs to configure their own environment to connect to Copilot. See [Configuring network settings for GitHub Copilot](/en/copilot/configuring-github-copilot/configuring-network-settings-for-github-copilot).

## [Copilot coding agent recommended allowlist](#copilot-coding-agent-recommended-allowlist)

The Copilot coding agent includes a built-in firewall with a recommended allowlist that is enabled by default. The recommended allowlist allows access to:

* Common operating system package repositories (for example, Debian, Ubuntu, Red Hat).
* Common container registries (for example, Docker Hub, Azure Container Registry, AWS Elastic Container Registry).
* Packages registries used by popular programming languages (C#, Dart, Go, Haskell, Java, JavaScript, Perl, PHP, Python, Ruby, Rust, Swift).
* Common certificate authorities (to allow SSL certificates to be validated).
* Hosts used to download web browsers for the Playwright MCP server.

For more information about configuring the Copilot coding agent firewall, see [Customizing or disabling the firewall for GitHub Copilot coding agent](/en/copilot/how-tos/use-copilot-agents/coding-agent/customize-the-agent-firewall).

The allowlist allows access to the following hosts:

### [Azure Infrastructure: Metadata Service](#azure-infrastructure-metadata-service)

* `168.63.129.16`

### [Certificate Authorities: DigiCert](#certificate-authorities-digicert)

* `crl3.digicert.com`
* `crl4.digicert.com`
* `ocsp.digicert.com`

### [Certificate Authorities: Symantec](#certificate-authorities-symantec)

* `ts-crl.ws.symantec.com`
* `ts-ocsp.ws.symantec.com`
* `s.symcb.com`
* `s.symcd.com`

### [Certificate Authorities: GeoTrust](#certificate-authorities-geotrust)

* `crl.geotrust.com`
* `ocsp.geotrust.com`

### [Certificate Authorities: Thawte](#certificate-authorities-thawte)

* `crl.thawte.com`
* `ocsp.thawte.com`

### [Certificate Authorities: VeriSign](#certificate-authorities-verisign)

* `crl.verisign.com`
* `ocsp.verisign.com`

### [Certificate Authorities: GlobalSign](#certificate-authorities-globalsign)

* `crl.globalsign.com`
* `ocsp.globalsign.com`

### [Certificate Authorities: SSL.com](#certificate-authorities-sslcom)

* `crls.ssl.com`
* `ocsp.ssl.com`

### [Certificate Authorities: IdenTrust](#certificate-authorities-identrust)

* `crl.identrust.com`
* `ocsp.identrust.com`

### [Certificate Authorities: Sectigo](#certificate-authorities-sectigo)

* `crl.sectigo.com`
* `ocsp.sectigo.com`

### [Certificate Authorities: UserTrust](#certificate-authorities-usertrust)

* `crl.usertrust.com`
* `ocsp.usertrust.com`

### [Container Registries: Docker](#container-registries-docker)

* `172.18.0.1`
* `ghcr.io`
* `registry.hub.docker.com`
* `*.docker.io`
* `*.docker.com`
* `production.cloudflare.docker.com`
* `auth.docker.io`
* `quay.io`
* `mcr.microsoft.com`
* `gcr.io`
* `public.ecr.aws`

### [GitHub: Content & API](#github-content--api)

* `*.githubusercontent.com`
* `raw.githubusercontent.com`
* `objects.githubusercontent.com`
* `lfs.github.com`
* `github-cloud.githubusercontent.com`
* `github-cloud.s3.amazonaws.com`
* `codeload.github.com`
* `scanning-api.github.com`
* `api.mcp.github.com`
* `uploads.github.com/copilot/chat/attachments/`

### [GitHub: Actions Artifact Storage](#github-actions-artifact-storage)

* `productionresultssa0.blob.core.windows.net`
* `productionresultssa1.blob.core.windows.net`
* `productionresultssa2.blob.core.windows.net`
* `productionresultssa3.blob.core.windows.net`
* `productionresultssa4.blob.core.windows.net`
* `productionresultssa5.blob.core.windows.net`
* `productionresultssa6.blob.core.windows.net`
* `productionresultssa7.blob.core.windows.net`
* `productionresultssa8.blob.core.windows.net`
* `productionresultssa9.blob.core.windows.net`
* `productionresultssa10.blob.core.windows.net`
* `productionresultssa11.blob.core.windows.net`
* `productionresultssa12.blob.core.windows.net`
* `productionresultssa13.blob.core.windows.net`
* `productionresultssa14.blob.core.windows.net`
* `productionresultssa15.blob.core.windows.net`
* `productionresultssa16.blob.core.windows.net`
* `productionresultssa17.blob.core.windows.net`
* `productionresultssa18.blob.core.windows.net`
* `productionresultssa19.blob.core.windows.net`

### [Programming Languages & Package Managers: C# / .NET](#programming-languages--package-managers-c--net)

* `nuget.org`
* `dist.nuget.org`
* `api.nuget.org`
* `nuget.pkg.github.com`
* `dotnet.microsoft.com`
* `pkgs.dev.azure.com`
* `builds.dotnet.microsoft.com`
* `dotnetcli.blob.core.windows.net`
* `nugetregistryv2prod.blob.core.windows.net`
* `azuresearch-usnc.nuget.org`
* `azuresearch-ussc.nuget.org`
* `dc.services.visualstudio.com`
* `dot.net`
* `download.visualstudio.microsoft.com`
* `dotnetcli.azureedge.net`
* `ci.dot.net`
* `www.microsoft.com`
* `oneocsp.microsoft.com`
* `www.microsoft.com/pkiops/crl/`

### [Programming Languages & Package Managers: Dart](#programming-languages--package-managers-dart)

* `pub.dev`
* `pub.dartlang.org`
* `storage.googleapis.com/pub-packages/`
* `storage.googleapis.com/dart-archive/`

### [Programming Languages & Package Managers: Go](#programming-languages--package-managers-go)

* `go.dev`
* `golang.org`
* `proxy.golang.org`
* `sum.golang.org`
* `pkg.go.dev`
* `goproxy.io`
* `storage.googleapis.com/proxy-golang-org-prod/`

### [Programming Languages & Package Managers: Haskell](#programming-languages--package-managers-haskell)

* `haskell.org`
* `*.hackage.haskell.org`
* `get-ghcup.haskell.org`
* `downloads.haskell.org`

### [Programming Languages & Package Managers: Java](#programming-languages--package-managers-java)

* `www.java.com`
* `jdk.java.net`
* `api.adoptium.net`
* `adoptium.net`
* `search.maven.org`
* `maven.apache.org`
* `repo.maven.apache.org`
* `repo1.maven.org`
* `maven.pkg.github.com`
* `maven-central.storage-download.googleapis.com`
* `maven.google.com`
* `maven.oracle.com`
* `jcenter.bintray.com`
* `oss.sonatype.org`
* `repo.spring.io`
* `gradle.org`
* `services.gradle.org`
* `plugins.gradle.org`
* `plugins-artifacts.gradle.org`
* `repo.grails.org`
* `download.eclipse.org`
* `download.oracle.com`

### [Programming Languages & Package Managers: Node.js / JavaScript](#programming-languages--package-managers-nodejs--javascript)

* `npmjs.org`
* `npmjs.com`
* `registry.npmjs.com`
* `registry.npmjs.org`
* `skimdb.npmjs.com`
* `npm.pkg.github.com`
* `api.npms.io`
* `nodejs.org`
* `yarnpkg.com`
* `registry.yarnpkg.com`
* `repo.yarnpkg.com`
* `deb.nodesource.com`
* `get.pnpm.io`
* `bun.sh`
* `deno.land`
* `registry.bower.io`
* `binaries.prisma.sh`

### [Programming Languages & Package Managers: Perl](#programming-languages--package-managers-perl)

* `cpan.org`
* `www.cpan.org`
* `metacpan.org`
* `cpan.metacpan.org`

### [Programming Languages & Package Managers: PHP](#programming-languages--package-managers-php)

* `repo.packagist.org`
* `packagist.org`
* `getcomposer.org`

### [Programming Languages & Package Managers: Python](#programming-languages--package-managers-python)

* `pypi.python.org`
* `pypi.org`
* `pip.pypa.io`
* `*.pythonhosted.org`
* `files.pythonhosted.org`
* `bootstrap.pypa.io`
* `conda.binstar.org`
* `conda.anaconda.org`
* `binstar.org`
* `anaconda.org`
* `download.pytorch.org`
* `repo.continuum.io`
* `repo.anaconda.com`

### [Programming Languages & Package Managers: Ruby](#programming-languages--package-managers-ruby)

* `rubygems.org`
* `api.rubygems.org`
* `rubygems.pkg.github.com`
* `bundler.rubygems.org`
* `gems.rubyforge.org`
* `gems.rubyonrails.org`
* `index.rubygems.org`
* `cache.ruby-lang.org`
* `*.rvm.io`

### [Programming Languages & Package Managers: Rust](#programming-languages--package-managers-rust)

* `crates.io`
* `index.crates.io`
* `static.crates.io`
* `sh.rustup.rs`
* `static.rust-lang.org`

### [Programming Languages & Package Managers: Swift](#programming-languages--package-managers-swift)

* `download.swift.org`
* `swift.org`
* `cocoapods.org`
* `cdn.cocoapods.org`

### [Infrastructure & Tools: HashiCorp](#infrastructure--tools-hashicorp)

* `releases.hashicorp.com`
* `apt.releases.hashicorp.com`
* `yum.releases.hashicorp.com`
* `registry.terraform.io`

### [Infrastructure & Tools: JSON Schema](#infrastructure--tools-json-schema)

* `json-schema.org`
* `json.schemastore.org`

### [Infrastructure & Tools: Playwright](#infrastructure--tools-playwright)

* `playwright.download.prss.microsoft.com`
* `cdn.playwright.dev`
* `playwright.azureedge.net`
* `playwright-akamai.azureedge.net`
* `playwright-verizon.azureedge.net`

### [Linux Package Managers: Ubuntu](#linux-package-managers-ubuntu)

* `archive.ubuntu.com`
* `security.ubuntu.com`
* `ppa.launchpad.net`
* `keyserver.ubuntu.com`
* `azure.archive.ubuntu.com`
* `api.snapcraft.io`

### [Linux Package Managers: Debian](#linux-package-managers-debian)

* `deb.debian.org`
* `security.debian.org`
* `keyring.debian.org`
* `packages.debian.org`
* `debian.map.fastlydns.net`
* `apt.llvm.org`

### [Linux Package Managers: Fedora](#linux-package-managers-fedora)

* `dl.fedoraproject.org`
* `mirrors.fedoraproject.org`
* `download.fedoraproject.org`

### [Linux Package Managers: CentOS](#linux-package-managers-centos)

* `mirror.centos.org`
* `vault.centos.org`

### [Linux Package Managers: Alpine](#linux-package-managers-alpine)

* `dl-cdn.alpinelinux.org`
* `pkg.alpinelinux.org`

### [Linux Package Managers: Arch](#linux-package-managers-arch)

* `mirror.archlinux.org`
* `archlinux.org`

### [Linux Package Managers: SUSE](#linux-package-managers-suse)

* `download.opensuse.org`

### [Linux Package Managers: Red Hat](#linux-package-managers-red-hat)

* `cdn.redhat.com`

### [Linux Package Managers: Common Package Sources](#linux-package-managers-common-package-sources)

* `packagecloud.io`
* `packages.cloud.google.com`
* `packages.microsoft.com`

### [Other](#other)

* `dl.k8s.io`
* `pkgs.k8s.io`

## [Further reading](#further-reading)

* [Network Connections in Visual Studio Code](https://code.visualstudio.com/docs/setup/network) in the Visual Studio documentation
* [Install and use Visual Studio and Azure Services behind a firewall or proxy server](https://learn.microsoft.com/en-us/visualstudio/install/install-and-use-visual-studio-behind-a-firewall-or-proxy-server) in the Microsoft documentation

## [Footnotes](#footnote-label)

1. Allows access to authorized users regardless of Copilot plan. Do not add this URL to your allowlist if you are using subscription-based network routing. For more information on subscription-based network routing, see [Managing GitHub Copilot access to your enterprise's network](/en/copilot/managing-copilot/managing-copilot-for-your-enterprise/managing-access-to-copilot-in-your-enterprise/managing-github-copilot-access-to-your-enterprises-network). [↩](#user-content-fnref-1)
2. Allows access to authorized users via a Copilot Individual plan. Do not add this URL to your allowlist if you are using subscription-based network routing. [↩](#user-content-fnref-2)
3. Allows access to authorized users via a Copilot Business plan. Do not add this URL to your allowlist if you want to use subscription-based network routing to block users from using Copilot Business on your network. [↩](#user-content-fnref-3)
4. Allows access to authorized users via a Copilot Enterprise plan. Do not add this URL to your allowlist if you want to use subscription-based network routing to block users from using Copilot Enterprise on your network. [↩](#user-content-fnref-4)

## Help and support

### Did you find what you needed?

Yes No

[Privacy policy](/en/site-policy/privacy-policies/github-privacy-statement)

### Help us make these docs great!

All GitHub docs are open source. See something that's wrong or unclear? Submit a pull request.

[Make a contribution](https://github.com/github/docs/blob/main/content/copilot/reference/copilot-allowlist-reference.md)

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
