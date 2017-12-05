<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>
<xsl:strip-space elements="type"/>

<!-- default rule -->
<xsl:template match="*" mode="conv24to35">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv24to35"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemeversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>2.4</literal> to <literal>3.5</literal>.
</para>
<xsl:template match="image" mode="conv24to35">
    <xsl:choose>
        <!-- nothing to do if already at 3.5 -->
        <xsl:when test="@schemaversion > 2.4 or @schemeversion > 2.4">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="3.5">
                <xsl:copy-of select="@*[local-name() != 'schemeversion']"/>
                <xsl:apply-templates mode="conv24to35"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- remove compressed element -->
<para xmlns="http://docbook.org/ns/docbook">
    Remove compressed element as it was moved into the type
</para>
<xsl:template match="node()|@*">
    <xsl:copy>
        <xsl:apply-templates select="node()|@*" mode="conv24to35"/>
    </xsl:copy>
</xsl:template>
<xsl:template match="compressed" mode="conv24to35"/>

</xsl:stylesheet>
