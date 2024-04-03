<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv73to74">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv73to74"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>7.3</literal> to <literal>7.4</literal>.
</para>
<xsl:template match="image" mode="conv73to74">
    <xsl:choose>
        <!-- nothing to do if already at 7.4 -->
        <xsl:when test="@schemaversion > 7.3">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="7.4">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv73to74"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- change packagemanager to apt if set to apt-get -->
<!-- change packagemanager to dnf if set to yum -->
<xsl:template match="packagemanager" mode="conv73to74">
    <xsl:choose>
        <xsl:when test="text()='apt-get'">
            <packagemanager>apt</packagemanager>
        </xsl:when>
        <xsl:when test="text()='yum'">
            <packagemanager>dnf</packagemanager>
        </xsl:when>
        <xsl:otherwise>
            <xsl:copy-of select="."/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
