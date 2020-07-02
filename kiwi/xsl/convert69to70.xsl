<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv69to70">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv69to70"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.9</literal> to <literal>7.0</literal>.
</para>
<xsl:template match="image" mode="conv69to70">
    <xsl:choose>
        <!-- nothing to do if already at 7.0 -->
        <xsl:when test="@schemaversion > 6.9">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="7.0">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv69to70"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- delete pxedeploy element from type -->
<xsl:template match="type/pxedeploy" mode="conv69to70">
</xsl:template>

</xsl:stylesheet>
