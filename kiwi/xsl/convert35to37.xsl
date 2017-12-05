<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xsl:stylesheet [
    <!ENTITY lowercase "'abcdefghijklmnopqrstuvwxyz'">
    <!ENTITY uppercase "'ABCDEFGHIJKLMNOPQRSTUVWXYZ'">
]>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv35to37">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv35to37"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>3.5</literal> to <literal>3.7</literal>.
</para>
<xsl:template match="image" mode="conv35to37">
    <xsl:choose>
        <!-- nothing to do if already at 3.7 -->
        <xsl:when test="@schemaversion > 3.5">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="3.7">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv35to37"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- update bool types -->
<para xmlns="http://docbook.org/ns/docbook">
    Change possible mixed cases into lowercase and
    normalize any whitespaces
</para>
<xsl:template name="oem-change-content" mode="conv35to37">
    <xsl:variable name="content"
        select="translate(normalize-space(.), &uppercase;, &lowercase;)"
    />
    <xsl:copy>
        <xsl:copy-of select="@*"/><!-- Copy attributes -->
        <xsl:choose>
            <xsl:when test="$content = 'false'">false</xsl:when>
            <xsl:when test="$content = 'true'">true</xsl:when>
            <xsl:when test="$content = 'yes'">true</xsl:when>
            <xsl:when test="$content = 'no'">false</xsl:when>
            <xsl:otherwise>
            <!-- Should not happen -->
            <xsl:message>Wrong value!</xsl:message>
        </xsl:otherwise>
        </xsl:choose>
    </xsl:copy>
</xsl:template>

<xsl:template match="oem-swap" mode="conv35to37">
    <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="oem-home" mode="conv35to37">
    <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="rpm-check-signatures" mode="conv35to37">
        <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="rpm-excludedocs" mode="conv35to37">
        <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="rpm-force" mode="conv35to37">
        <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="oem-recovery" mode="conv35to37">
        <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="oem-kiwi-initrd" mode="conv35to37">
        <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="oem-sap-install" mode="conv35to37">
        <xsl:call-template name="oem-change-content"/>
</xsl:template>

<xsl:template match="oem-reboot" mode="conv35to37">
        <xsl:call-template name="oem-change-content"/>
</xsl:template>

</xsl:stylesheet>
