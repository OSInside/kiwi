<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>
<xsl:strip-space elements="preferences"/>

<!-- default rule -->
<xsl:template match="*" mode="conv38to39">
        <xsl:copy>
                <xsl:copy-of select="@*"/>
                     <xsl:apply-templates mode="conv38to39"/>
        </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>3.8</literal> to <literal>3.9</literal>.
</para>
<xsl:template match="image" mode="conv38to39">
    <xsl:choose>
        <!-- nothing to do if already at 3.9 -->
        <xsl:when test="@schemaversion > 3.8">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="3.9">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv38to39"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv38to39">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv38to39"/>
    </xsl:copy>
</xsl:template>

<!-- create new element oemconfig -->
<para xmlns="http://docbook.org/ns/docbook">
    Create new <tag class="element">oemconfig</tag> element to collect
    all <tag class="element">oem-*</tag> elements in one place and remove 
    them from the <tag class="element">preferences</tag> element.
</para>
<xsl:template match="image" mode="conv38to39">
    <xsl:variable name="boottitle" select="/image/preferences/oem-boot-title"/>
    <xsl:variable name="home" select="/image/preferences/oem-home"/>
    <xsl:variable name="initrd" select="/image/preferences/oem-kiwi-initrd"/>
    <xsl:variable name="reboot" select="/image/preferences/oem-reboot"/>
    <xsl:variable name="inplace" select="/image/preferences/oem-inplace-recovery"/>
    <xsl:variable name="align" select="/image/preferences/oem-align-partition"/>
    <xsl:variable name="recovery" select="/image/preferences/oem-recovery"/>
    <xsl:variable name="dumphalt" select="/image/preferences/oem-dumphalt"/>
    <xsl:variable name="recoveryid" select="/image/preferences/oem-recoveryID"/>
    <xsl:variable name="sapinstall" select="/image/preferences/oem-sap-install"/>
    <xsl:variable name="swap" select="/image/preferences/oem-swap"/>
    <xsl:variable name="swapsize" select="/image/preferences/oem-swapsize"/>
    <xsl:variable name="systemsize" select="/image/preferences/oem-systemsize"/>
    <image>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv38to39"/>

        <xsl:if test="$boottitle or $home or $initrd or $reboot or $recovery or $recoveryid or $sapinstall or $swap or $swapsize or $systemsize">
            <oemconfig>
                <xsl:copy-of select="$boottitle"/>
                <xsl:copy-of select="$home"/>
                <xsl:copy-of select="$initrd"/>
                <xsl:copy-of select="$reboot"/>
                <xsl:copy-of select="$align"/>
                <xsl:copy-of select="$inplace"/>
                <xsl:copy-of select="$recovery"/>
                <xsl:copy-of select="$recoveryid"/>
                <xsl:copy-of select="$sapinstall"/>
                <xsl:copy-of select="$swap"/>
                <xsl:copy-of select="$swapsize"/>
                <xsl:copy-of select="$systemsize"/>
                <xsl:copy-of select="$dumphalt"/>
            </oemconfig>
        </xsl:if>
    </image>
</xsl:template>

<!-- swallow the output for the OEM settings in their current position -->
<xsl:template match="preferences/oem-boot-title" mode="conv38to39"/>
<xsl:template match="preferences/oem-home" mode="conv38to39"/>
<xsl:template match="preferences/oem-kiwi-initrd" mode="conv38to39"/>
<xsl:template match="preferences/oem-reboot" mode="conv38to39"/>
<xsl:template match="preferences/oem-inplace-recovery" mode="conv38to39"/>
<xsl:template match="preferences/oem-align-partition" mode="conv38to39"/>
<xsl:template match="preferences/oem-recovery" mode="conv38to39"/>
<xsl:template match="preferences/oem-recoveryID" mode="conv38to39"/>
<xsl:template match="preferences/oem-sap-install" mode="conv38to39"/>
<xsl:template match="preferences/oem-swap" mode="conv38to39"/>
<xsl:template match="preferences/oem-swapsize" mode="conv38to39"/>
<xsl:template match="preferences/oem-systemsize" mode="conv38to39"/>
<xsl:template match="preferences/oem-dumphalt" mode="conv38to39"/>

</xsl:stylesheet>
