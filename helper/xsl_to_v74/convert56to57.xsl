<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv56to57">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv56to57"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.6</literal> to <literal>5.7</literal>.
</para>
<xsl:template match="image" mode="conv56to57">
    <xsl:choose>
        <!-- nothing to do if already at 5.7 -->
        <xsl:when test="@schemaversion > 5.6">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.7">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv56to57"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv56to57">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv56to57"/>
    </xsl:copy>
</xsl:template>

<!-- transform the opensusePattern element into a namedCollection -->
<xsl:template match="packages/opensusePattern" mode="conv56to57">
    <namedCollection>
        <xsl:copy-of select="@*"/>
    </namedCollection>
</xsl:template>

<!-- transform the rhelGroup element into a namedCollection -->
<xsl:template match="packages/rhelGroup" mode="conv56to57">
    <namedCollection>
        <xsl:copy-of select="@*"/>
    </namedCollection>
</xsl:template>

</xsl:stylesheet>
