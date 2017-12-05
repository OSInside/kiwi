<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
    indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv60to61">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv60to61"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.0</literal> to <literal>6.1</literal>.
</para>
<xsl:template match="image" mode="conv60to61">
    <xsl:choose>
        <!-- nothing to do if already at 6.1 -->
        <xsl:when test="@schemaversion > 6.0">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.1">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates mode="conv60to61"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- rename opensuseProduct -->
<para xmlns="http://docbook.org/ns/docbook">
    Change section opensuseProduct to product
</para>
<xsl:template match="opensuseProduct" mode="conv60to61">
    <product>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv60to61"/>
    </product>
</xsl:template>

</xsl:stylesheet>
