<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv67to68">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv67to68"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.7</literal> to <literal>6.8</literal>.
</para>
<xsl:template match="image" mode="conv67to68">
    <xsl:choose>
        <!-- nothing to do if already at 6.8 -->
        <xsl:when test="@schemaversion > 6.7">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.8">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv67to68"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv67to68">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv67to68"/>
    </xsl:copy>
</xsl:template>

<!-- Delete hwclock section -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete hwclock section
</para>
<xsl:template match="hwclock" mode="conv67to68">
    <xsl:apply-templates select="*" mode="conv67to68"/>
</xsl:template>

</xsl:stylesheet>
