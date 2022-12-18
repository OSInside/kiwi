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
Provides a KIWI runtime config file suitable building
the fedora based integrations test

%prep
%setup -q

%install
install -D -m 644 kiwi-settings/kiwi.yml %{buildroot}/etc/kiwi.yml

%files
%defattr(-,root,root)
%config /etc/kiwi.yml

%changelog
