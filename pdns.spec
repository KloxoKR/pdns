#
# PowerDNS server el7 spec file
#
%global _hardened_build 1

Summary:		PowerDNS is a Versatile Database Driven Nameserver
Name:			pdns
Version:		4.1.13
Release:		3.kkr%{dist}
Epoch:			0
License:		GPLv2
Group:			System Environment/Daemons
URL:			http://www.powerdns.com/
Source0:		http://downloads.powerdns.com/releases/pdns-4.1.13.tar.bz2
Source1:		pdns.service
Patch0:			pdns-4.1.1-disable-secpoll.patch

BuildRequires:		systemd-units
BuildRequires:		systemd-devel
BuildRequires:		gcc
BuildRequires:		gcc-c++
BuildRequires:		krb5-devel
BuildRequires:		boost-devel
BuildRequires:		sqlite-devel
BuildRequires:		lua-devel
BuildRequires:		protobuf-devel
BuildRequires:		openssl-devel

Requires(pre):		shadow-utils
Requires(post):		systemd-sysv
Requires(post):		systemd-units
Requires(preun):	systemd-units
Requires(postun):	systemd-units
Provides:		powerdns = %{version}-%{release}

%description
PowerDNS is a versatile nameserver which supports a large number
of different backends ranging from simple zonefiles to relational
databases and load balancing/failover algorithms.

%package		backend-bind
Summary:		Bind backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}

%description		backend-bind
The BindBackend parses a Bind-style named.conf and extracts information about
zones from it. It makes no attempt to honour other configuration flags,
which you should configure (when available) using the PDNS native configuration.

%package		backend-mysql
Summary:		MySQL backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}
BuildRequires:		mysql-devel

%description		backend-mysql
This package contains the MySQL backend for the PowerDNS nameserver.

%package		backend-postgresql
Summary:		postgesql backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}
BuildRequires:		postgresql-devel

%description		backend-postgresql
This package contains the postgesql backend for the PowerDNS nameserver.

%package		backend-sqlite
Summary:		sqlite3 backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}

%description		backend-sqlite
This package contains the sqlite3 backend for the PowerDNS nameserver.

%package		backend-ldap
Summary:		LDAP backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}
BuildRequires:		openldap-devel

%description		backend-ldap
This package contains the LDAP backend for the PowerDNS nameserver.

%package		backend-lua
Summary:		Lua backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{version}-%{release}
BuildRequires:		lua-devel

%description		backend-lua
This package contains the Lua backent for the PowerDNS nameserver.

%package		backend-mydns
Summary:		MyDNS backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}
BuildRequires:		mysql-devel

%description		backend-mydns
This package contains the MyDNS backend for the PowerDNS nameserver.

%package		backend-pipe
Summary:		Pipe/coprocess backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}

%description		backend-pipe
This package contains the pipe backend for the PowerDNS nameserver. This
allows PowerDNS to retrieve domain info from a process that accepts
questions on stdin and returns answers on stdout.

%package		backend-remote
Summary:		Experimental remotere backend for %{name}
Group:			System Environment/Daemons
Requires:		%{name}%{?_isa} = %{epoch}:%{version}-%{release}

%description		backend-remote
This package contains the remote backend for the PowerDNS nameserver. This
backend provides json based unix socket / pipe / http remoting for powerdns.

%package		tools
Summary:		PowerDNS DNS tools
Group:			Applications/System
Conflicts:		%{name} < %{epoch}:%{version}-%{release}
Conflicts:		%{name} > %{epoch}:%{version}-%{release}

%description		tools
This package contains the the PowerDNS DNS tools.

%prep
%setup -q -n pdns-4.1.13
%patch0 -p1 -b .disable-secpoll

%build
%configure \
    --sysconfdir=%{_sysconfdir}/%{name} \
    --with-sqlite3 \
    --with-lua \
    --with-protobuf \
    --with-modules="" \
    --with-dynmodules="bind gmysql gpgsql gsqlite3 ldap lua mydns pipe remote" \
    --disable-static \
    --enable-tools

sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

%{__make} %{?_smp_mflags}

%install
%{__make} DESTDIR=%{buildroot} install
%{__rm} -f %{buildroot}%{_libdir}/%{name}/*.la

install -d %{buildroot}%{_sysconfdir}/%{name}/

# fix the config
%{__mv} %{buildroot}%{_sysconfdir}/%{name}/pdns.conf-dist %{buildroot}%{_sysconfdir}/%{name}/pdns.conf

cat >> %{buildroot}%{_sysconfdir}/%{name}/pdns.conf << EOF
setuid=pdns
setgid=pdns
EOF

chmod 600 %{buildroot}%{_sysconfdir}/%{name}/pdns.conf

# install our systemd service file
%{__rm} -f %{buildroot}%{_unitdir}/pdns.service
%{__rm} -f %{buildroot}%{_unitdir}/pdns@.service
install -p -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/pdns.service

%pre
getent group pdns >/dev/null || groupadd -r pdns
getent passwd pdns >/dev/null || \
	useradd -r -g pdns -d / -s /sbin/nologin \
	-c "PowerDNS authoritative server user" pdns
exit 0

%post
%systemd_post pdns.service

%preun
%systemd_preun pdns.service

%postun
%systemd_postun_with_restart pdns.service

%files
%doc COPYING INSTALL NOTICE README
%dir %{_sysconfdir}/%{name}/
%dir %{_libdir}/%{name}/
%config(noreplace) %attr(0600,root,root) %{_sysconfdir}/%{name}/pdns.conf
%{_unitdir}/pdns.service
%{_bindir}/pdns_control
%{_bindir}/pdnsutil
%{_sbindir}/pdns_server
%{_mandir}/man1/pdns_control.1.gz
%{_mandir}/man1/pdns_server.1.gz
%{_mandir}/man1/pdnsutil.1.gz

%files backend-bind
%{_libdir}/%{name}/libbindbackend.so
%doc pdns/bind-dnssec.schema.sqlite3.sql

%files backend-mysql
%{_libdir}/%{name}/libgmysqlbackend.so
%doc %{_defaultdocdir}/%{name}/schema.mysql.sql
%doc %{_defaultdocdir}/%{name}/nodnssec-3.x_to_3.4.0_schema.mysql.sql
%doc %{_defaultdocdir}/%{name}/dnssec-3.x_to_3.4.0_schema.mysql.sql
%doc %{_defaultdocdir}/%{name}/3.4.0_to_4.1.0_schema.mysql.sql

%files backend-postgresql
%{_libdir}/%{name}/libgpgsqlbackend.so
%doc %{_defaultdocdir}/%{name}/schema.pgsql.sql
%doc %{_defaultdocdir}/%{name}/nodnssec-3.x_to_3.4.0_schema.pgsql.sql
%doc %{_defaultdocdir}/%{name}/dnssec-3.x_to_3.4.0_schema.pgsql.sql
%doc %{_defaultdocdir}/%{name}/3.4.0_to_4.1.0_schema.pgsql.sql
%doc %{_defaultdocdir}/%{name}/4.1.10_to_4.1.11.schema.pgsql.sql

%files backend-sqlite
%{_libdir}/%{name}/libgsqlite3backend.so
%doc %{_defaultdocdir}/%{name}/schema.sqlite3.sql
%doc %{_defaultdocdir}/%{name}/nodnssec-3.x_to_3.4.0_schema.sqlite3.sql
%doc %{_defaultdocdir}/%{name}/dnssec-3.x_to_3.4.0_schema.sqlite3.sql

%files backend-ldap
%{_libdir}/%{name}/libldapbackend.so
%doc %{_defaultdocdir}/%{name}/dnsdomain2.schema
%doc %{_defaultdocdir}/%{name}/pdns-domaininfo.schema

%files backend-lua
%{_libdir}/%{name}/libluabackend.so
%doc modules/luabackend/README

%files backend-mydns
%{_libdir}/%{name}/libmydnsbackend.so
%doc %{_defaultdocdir}/%{name}/schema.mydns.sql

%files backend-pipe
%{_libdir}/%{name}/libpipebackend.so

%files backend-remote
%{_libdir}/%{name}/libremotebackend.so

%files tools
%{_bindir}/zone2json
%{_bindir}/zone2ldap
%{_bindir}/zone2sql
 %{_bindir}/calidns
 %{_bindir}/dnsbulktest
 %{_bindir}/dnsgram
 %{_bindir}/dnsreplay
 %{_bindir}/dnsscan
 %{_bindir}/dnsscope
 %{_bindir}/dnstcpbench
 %{_bindir}/dnswasher
 %{_bindir}/dumresp
 %{_bindir}/ixplore
 %{_bindir}/nproxy
 %{_bindir}/nsec3dig
 %{_bindir}/pdns_notify
 %{_bindir}/dnspcap2protobuf
 %{_bindir}/saxfr
 %{_bindir}/sdig
 %{_bindir}/stubquery
%{_mandir}/man1/zone2json.1.gz
%{_mandir}/man1/zone2ldap.1.gz
%{_mandir}/man1/zone2sql.1.gz
 %{_mandir}/man1/calidns.1.gz
 %{_mandir}/man1/dnsbulktest.1.gz
 %{_mandir}/man1/dnsgram.1.gz
 %{_mandir}/man1/dnsreplay.1.gz
 %{_mandir}/man1/dnsscan.1.gz
 %{_mandir}/man1/dnsscope.1.gz
 %{_mandir}/man1/dnstcpbench.1.gz
 %{_mandir}/man1/dnswasher.1.gz
 %{_mandir}/man1/dumresp.1.gz
 %{_mandir}/man1/ixplore.1.gz
 %{_mandir}/man1/nproxy.1.gz
 %{_mandir}/man1/nsec3dig.1.gz
 %{_mandir}/man1/pdns_notify.1.gz
 %{_mandir}/man1/dnspcap2protobuf.1.gz
 %{_mandir}/man1/saxfr.1.gz
 %{_mandir}/man1/sdig.1.gz


%changelog
* Fri Mar 27 2020 Dionysis Kladis <dkstiler@gmail.com> 4.1.13-3.kng
- Added  openssl for secure dns comminication

* Mon Dec 23 2019 John Pierce <john@luckytanuki.com> 4.1.13-2.kng
- Build for Kloxo NG

* Thu Aug 08 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.13-1
- update to version 4.1.13

* Wed Aug 07 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.12-1
- update to version 4.1.12

* Tue Jul 30 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.11-1
- update to version 4.1.11

* Thu Jun 20 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.10-1
- update to version 4.1.10

* Tue Jun 18 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.9-1
- update to version 4.1.9

* Fri Mar 22 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.8-1
- update to version 4.1.8

* Mon Mar 18 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.7-1
- update to version 4.1.7

* Wed Jan 30 2019 Kees Monshouwer <mind04@monshouwer.org> 4.1.6-1
- update to version 4.1.6

* Tue Nov 06 2018 Kees Monshouwer <mind04@monshouwer.org> 4.1.5-1
- update to version 4.1.5

* Wed Aug 29 2018 Kees Monshouwer <mind04@monshouwer.org> 4.1.4-1
- update to version 4.1.4

* Thu May 24 2018 Kees Monshouwer <mind04@monshouwer.org> 4.1.3-1
- update to version 4.1.3

* Mon May 07 2018 Kees Monshouwer <mind04@monshouwer.org> 4.1.2-1
- update to version 4.1.2

* Fri Feb 16 2018 Kees Monshouwer <mind04@monshouwer.org> 4.1.1-1
- update to version 4.1.1

* Thu Nov 30 2017 Kees Monshouwer <mind04@monshouwer.org> 4.1.0-1
- update to version 4.1.0

* Mon Nov 27 2017 Kees Monshouwer <mind04@monshouwer.org> 4.0.5-1
- update to version 4.0.5

* Thu Jun 22 2017 Kees Monshouwer <mind04@monshouwer.org> 4.0.4-1
- update to version 4.0.4

* Tue Jan 17 2017 Kees Monshouwer <mind04@monshouwer.org> 4.0.3-1
- update to version 4.0.3

* Fri Jan 13 2017 Kees Monshouwer <mind04@monshouwer.org> 4.0.2-1
- update to version 4.0.2

* Fri Jul 29 2016 Kees Monshouwer <mind04@monshouwer.org> 4.0.1-1
- update to version 4.0.1

* Mon Jul 11 2016 Kees Monshouwer <mind04@monshouwer.org> 4.0.0-1
- update to version 4.0.0
- add ixplore, sdig and dnspcap2protobuf to tools
- rename pdnssec to pdnsutil
- remove geo backend

* Thu Aug 27 2015 Kees Monshouwer <mind04@monshouwer.org> 3.4.6-1
- update to version 3.4.6

* Tue Jun 09 2015 Kees Monshouwer <mind04@monshouwer.org> 3.4.5-1
- update to version 3.4.5

* Thu Apr 23 2015 Kees Monshouwer <mind04@monshouwer.org> 3.4.4-1
- update to version 3.4.4

* Mon Mar 02 2015 Kees Monshouwer <mind04@monshouwer.org> 3.4.3-1
- update to version 3.4.3

* Tue Feb 03 2015 Kees Monshouwer <mind04@monshouwer.org> 3.4.2-1
- update to version 3.4.2
- move all manpages to section 1
- markdown based documentation

* Thu Oct 30 2014 Kees Monshouwer <mind04@monshouwer.org> 3.4.1-1
- update to 3.4.1
- disable security status polling by default https://github.com/PowerDNS/pdns/blob/master/pdns/docs/security-poll.md

* Sat Oct 11 2014 Kees Monshouwer <mind04@monshouwer.org> 3.4.0-2
- reorder spec file
- rename backend-sqlite3 to backend-sqlite
- add lua backend

* Tue Sep 30 2014 Kees Monshouwer <mind04@monshouwer.org> 3.4.0-1
- initial el7 build for PowerDNS server
