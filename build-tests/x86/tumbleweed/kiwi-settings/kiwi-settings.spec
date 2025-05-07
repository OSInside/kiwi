Name:           kiwi-settings
Version:        1.1.1
Release:        0
License:        GPL-3.0-or-later
%if "%{_vendor}" == "debbuild"
Packager:       Marcus Schaefer <marcus.schaefer@gmail.com>
%endif
Summary:        KIWI - runtime config file
Group:          System/Management
Source:         %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
BuildArch:      noarch

%description
Provides a KIWI runtime config file and others suitable
for building the tumbleweed based integrations test

%prep
%setup -q

%install
mkdir -p %{buildroot}/etc/modprobe.d
cp -a kiwi-settings/60-blacklist_fs-erofs.conf %{buildroot}/etc/modprobe.d/

%files
%defattr(-,root,root)
/etc/modprobe.d/60-blacklist_fs-erofs.conf

%changelog
