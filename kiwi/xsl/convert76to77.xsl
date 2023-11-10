<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv76to77">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv76to77"/>
    </xsl:copy>
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>7.6</literal> to <literal>7.7</literal>.
</para>
<xsl:template match="image" mode="conv76to77">
    <xsl:choose>
        <!-- nothing to do if already at 7.7 -->
        <xsl:when test="@schemaversion > 7.6">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="7.7">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv75to76"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

</xsl:stylesheet>
